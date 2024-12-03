import re
import json
import os
from typing import Dict, List, Tuple, Any, Optional


class LogParser:

    def __init__(self, filename: str):
        self.filename = filename
        self.content = self._read_file()
        self.players = []
        self.messages = []
        self.timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})'

    def _read_file(self) -> str:
        """读取日志文件"""
        if not os.path.exists(self.filename):
            return ""
        with open(self.filename, 'r', encoding='utf-8') as f:
            return f.read()

    def _parse_game_setup(self) -> None:
        """解析游戏设置信息"""
        setup_pattern = r"Game setup:\n((?:Player\d+: [^,]+,\n?)+)"
        setup_match = re.search(setup_pattern, self.content)

        if setup_match:
            player_pattern = r"Player(\d+): ([^,]+),"
            for match in re.finditer(player_pattern, setup_match.group(1)):
                player_id = int(match.group(1))
                role = match.group(2).strip()
                self.players.append({
                    "id": player_id,
                    "name": f"Player{player_id}",
                    "role": role,
                    "avatar": f"/public/avatars/{role}.jpg",
                    "win": 0,
                    "loss": 0
                })

        # 添加主持人
        self.players.append({
            "id": 0,
            "name": "Moderator",
            "role": "Moderator"
        })

    def _determine_message_type(self, speaker: str, message: str,
                                role: str) -> str:
        """判断消息类型"""
        if speaker == "Moderator":
            if any(keyword in message.lower()
                   for keyword in ["choose", "who", "would you like"]):
                return "Question"
            if "understood" in message.lower():
                return "Confirmation"
            if any(keyword in message.lower()
                   for keyword in ["killed", "eliminated", "game over"]):
                return "Announcement"
            return "Instruction"

        if "ready to" in message:
            return "Preparation"
        if any(action in message for action in [
                "vote to eliminate", "Hunt", "Protect", "Verify", "Poison",
                "Save", "Pass"
        ]):
            return "Action"

        return "Say"

    def _clean_json_content(self, content: str) -> Tuple[str, List[str]]:
        """清理JSON内容"""
        # 移除INFO/ERROR等日志行
        log_lines = re.findall(
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| (?:INFO|ERROR|WARNING).*?\n',
            content)
        cleaned = re.sub(
            r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \| (?:INFO|ERROR|WARNING).*?\n',
            '', content)
        # 移除空行
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        return cleaned, log_lines

    def _parse_messages(self) -> None:
        """解析所有消息"""
        # 提取所有时间戳行和它们的位置
        timestamps = [
            (m.group(1), m.start())
            for m in re.finditer(self.timestamp_pattern, self.content)
        ]

        # 解析JSON块
        json_pattern = r'{\s*"ROLE":[^{]*?"RESPONSE":\s*"[^"]*"[^}]*?}'
        json_matches = list(re.finditer(json_pattern, self.content, re.DOTALL))
        json_positions = [(m.start(), m.end()) for m in json_matches]

        # 函数用于检查位置是否在任何JSON块内
        def is_in_json_block(pos):
            return any(start <= pos <= end for start, end in json_positions)

        def is_valid_message(message, speaker, role):
            # 如果消息只包含时间戳，则不是有效消息
            if not message or not speaker or not role:
                return False

            # 清理时间戳
            cleaned_message = re.sub(self.timestamp_pattern, '',
                                     message).strip()

            # 检查清理后的消息是否为空或者只包含特定的角色名
            if not cleaned_message or cleaned_message in [
                    'Moderator', 'Seer', 'Witch', 'Guard', 'Werewolf',
                    'Villager'
            ]:
                return False

            return True

        # 处理所有常规消息
        message_pattern = r'(?:' + self.timestamp_pattern + r' \| (?:INFO|ERROR|WARNING).*? - )?(Player\d+|Moderator)\((\w+)\):\s*(.*?)(?=(?:\n\d{4}-\d{2}-\d{2}|\n(?:Player\d+|Moderator)\(|\n{|$))'

        for match in re.finditer(message_pattern, self.content, re.DOTALL):
            start_pos = match.start()

            # 跳过JSON块中的匹配
            if is_in_json_block(start_pos):
                continue

            speaker = match.group(1)
            role = match.group(2)
            message = match.group(3).strip()

            # 获取最近的时间戳
            timestamp = next((ts[0] for ts in timestamps if ts[1] < start_pos),
                             None)

            # 清理消息中的时间戳
            if timestamp:
                message = message.replace(timestamp, '').strip()

            # 只添加有效的消息
            if is_valid_message(message, speaker, role):
                msg_type = self._determine_message_type(speaker, message, role)
                self.messages.append({
                    "timestamp": timestamp,
                    "position": start_pos,
                    "data": {
                        "speaker": speaker,
                        "content": message,
                        "type": msg_type,
                        "role": role
                    }
                })

        # 处理JSON块
        for match in json_matches:
            json_content = match.group()
            start_pos = match.start()

            # 清理JSON内容并获取日志行
            cleaned_json, log_lines = self._clean_json_content(json_content)

            # 处理日志行
            self._process_log_lines(log_lines, timestamps)

            try:
                data = json.loads(cleaned_json)
                timestamp = next(
                    (ts[0] for ts in timestamps if ts[1] < start_pos), None)

                if "THOUGHTS" in data:
                    self.messages.append({
                        "timestamp": timestamp,
                        "position": start_pos,
                        "data": {
                            "speaker": data.get("PLAYER_NAME", "Unknown"),
                            "content": data["THOUGHTS"],
                            "type": "Thought",
                            "role": data.get("ROLE", ""),
                            "player_name": data.get("PLAYER_NAME", ""),
                            "living_players": data.get("LIVING_PLAYERS", [])
                        }
                    })

                if "RESPONSE" in data:
                    self.messages.append({
                        "timestamp": timestamp,
                        "position": start_pos + 1,
                        "data": {
                            "speaker": data.get("PLAYER_NAME", "Unknown"),
                            "content": data["RESPONSE"],
                            "type": "Response",
                            "role": data.get("ROLE", ""),
                            "player_name": data.get("PLAYER_NAME", ""),
                            "living_players": data.get("LIVING_PLAYERS", [])
                        }
                    })
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON at position {start_pos}: {e}")

    def _process_log_lines(self, log_lines: List[str],
                           timestamps: List[Tuple[str, int]]) -> None:
        """处理日志行"""
        for log_line in log_lines:
            # 提取玩家消息
            player_msg_match = re.search(
                r'(Player\d+|Moderator)\((\w+)\):\s*(.*?)$', log_line)
            if player_msg_match:
                speaker = player_msg_match.group(1)
                role = player_msg_match.group(2)
                message = player_msg_match.group(3).strip()

                msg_type = self._determine_message_type(speaker, message, role)
                timestamp = re.match(self.timestamp_pattern, log_line)

                if timestamp:
                    self.messages.append({
                        "timestamp":
                        timestamp.group(1),
                        "position":
                        self.content.find(log_line),
                        "data": {
                            "speaker": speaker,
                            "content": message,
                            "type": msg_type,
                            "role": role
                        }
                    })

    def _parse_game_result(self) -> int:
        """解析游戏结果"""
        current_round = 0
        result_pattern = r"Game over! (.*?)\n"
        match = re.search(result_pattern, self.content,
                          re.DOTALL | re.IGNORECASE)

        if match:
            current_round += 1
            result = match.group(1)
            is_good_guys_win = "good guys" in result.lower()

            # 添加这条消息到对话中
            self.messages.append({
                "timestamp": None,  # 或者可以找到最近的时间戳
                "position": match.start(),
                "data": {
                    "speaker": "Moderator",
                    "content": f"Game over! {result}",
                    "type": "Announcement",
                    "role": "Moderator"
                }
            })

            for player in self.players:
                if player["role"] == "Moderator":
                    continue
                is_good = player["role"] not in ["Werewolf"]
                if is_good == is_good_guys_win:
                    player["win"] += 1
                else:
                    player["loss"] += 1

        return current_round

    def _get_game_rounds(self) -> int:
        """获取游戏总轮数"""
        name_parts = self.filename.split('/')[-1].split('.')[0].split('_')
        if len(name_parts) >= 2:
            try:
                return int(name_parts[1])
            except ValueError:
                return 0
        return 0

    def _replace_player_names(self, names: List[str]) -> None:
        """Replace Player1, Player2, etc. with actual names"""
        # Create a mapping of player numbers to names
        name_mapping = {}
        for i, name in enumerate(names, 1):
            name_mapping[f"Player{i}"] = name[:10]

        # Update players list
        for player in self.players:
            if player["name"] in name_mapping:
                player["name"] = name_mapping[player["name"]]
                # Update avatar path if it exists
                if "avatar" in player:
                    player["avatar"] = player["avatar"].replace(f"Player{player['id']}", name_mapping[f"Player{player['id']}"])

        # Update dialogue entries
        for message in self.dialogue:
            # Update speaker
            if message["speaker"] in name_mapping:
                message["speaker"] = name_mapping[message["speaker"]]
            
            # Update content - replace all occurrences of Player1, Player2, etc.
            content = message["content"]
            for player_num, name in name_mapping.items():
                content = re.sub(rf'\b{player_num}\b', name, content)
            message["content"] = content

            # Update player_name if it exists
            if "player_name" in message and message["player_name"] in name_mapping:
                message["player_name"] = name_mapping[message["player_name"]]
            
            # Update living_players if it exists
            if "living_players" in message:
                message["living_players"] = [
                    name_mapping.get(player, player) 
                    for player in message["living_players"]
                ]

    def parse(self, names: Optional[List[str]] = None) -> Dict[str, Any]:
        """解析日志文件并返回结果"""
        if not self.content:
            return {
                "players": [],
                "dialogue": [],
                "n_rounds": 0,
                "current_round": 0
            }

        # 解析游戏设置
        self._parse_game_setup()

        # 解析消息
        self._parse_messages()

        # 获取游戏轮数
        n_rounds = self._get_game_rounds()

        # 解析游戏结果
        current_round = self._parse_game_result()

        # 按时间戳和位置排序消息
        # self.messages.sort(key=lambda x: (x["timestamp"] or "", x["position"]))
        self.messages.sort(key=lambda x: (x["position"]))

        # 提取排序后的对话数据
        self.dialogue = [msg["data"] for msg in self.messages]

        if names:
            self._replace_player_names(names)

        return {
            "players": self.players,
            "dialogue": self.dialogue,
            "n_rounds": n_rounds,
            "current_round": current_round
        }


def parse_log_file(filename: str, names: Optional[List[str]] = None) -> Dict[str, Any]:
    """解析日志文件的主函数"""
    parser = LogParser(filename)
    return parser.parse(names)


def test_parser(filename: str, names: Optional[List[str]] = None) -> None:
    """测试解析器"""
    game_data = parse_log_file(filename, names)

    print("\nPlayers:")
    for player in game_data["players"]:
        if player["role"] == "Moderator":
            print(f"{player['name']}: {player['role']}")
        else:
            print(
                f"{player['name']}: {player['role']}, win: {player['win']}, loss: {player['loss']}"
            )

    print("\nDialogue count:", len(game_data["dialogue"]))

    print("\nMessage types distribution:")
    type_count = {}
    for entry in game_data["dialogue"]:
        type_count[entry["type"]] = type_count.get(entry["type"], 0) + 1
    for msg_type, count in sorted(type_count.items()):
        print(f"{msg_type}: {count}")

    print("\nDialogue entries:")
    for i, entry in enumerate(game_data["dialogue"], 1):
        print(
            f"{i}. [{entry['speaker']}] ({entry['type']}): {entry['content']}")


if __name__ == "__main__":
    names = ['Kupo','GaryChia380460','Sczwt','nft2great','nftflair','ggbak',
              'iDominoes','Mirou_Bouguerba','mferPalace','joltikahedron','kenthecaffiend']
    test_parser("output_1_11_Group1.txt", names)
