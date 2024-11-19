import re
import json
from flask import current_app
import ipdb


def clean_json_content(content):
    """清理JSON内容,移除时间戳行并返回干净的JSON文本和提取出的日志行"""
    # 匹配时间戳开头的行
    timestamp_pattern = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}.*?\n'

    # 提取所有日志行
    log_lines = re.finditer(timestamp_pattern, content)
    extracted_logs = [match.group() for match in log_lines]

    # 移除JSON中的日志行
    cleaned_content = re.sub(timestamp_pattern, '', content)

    return cleaned_content, extracted_logs


def parse_log_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    current_round = 0
    name_l = filename.split('/')[-1].split('.')[0].split('_')
    assert len(name_l) == 3, f"文件名格式错误{name_l}"
    n_rounds = int(name_l[1])
    n_players = int(name_l[2])

    # 1. 提取玩家设置信息
    setup_pattern = r"Game setup:"
    # 根据玩家数量动态构建匹配模式
    for i in range(1, n_players + 1):
        setup_pattern += fr"\s*Player{i}: ([^,]+),"
    setup_match = re.search(setup_pattern, content)

    players = []
    if setup_match:
        roles = setup_match.groups()
        for i, role in enumerate(roles, 1):
            players.append({
                "id": i,
                "name": f"Player{i}",
                "role": role.strip(),
                "avatar": f"/public/avatars/{role.strip()}.jpg",
                "loss": 0,
                "win": 0
            })

    players.append({
        "id": 0,
        "name": "Moderator",
        "role": "Moderator",
    })

    # 2. 提取带有位置信息的对话
    messages = []

    # 提取所有时间戳行和它们的位置
    timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})'
    timestamps = [(m.group(1), m.start())
                  for m in re.finditer(timestamp_pattern, content)]

    # 处理JSON块
    json_pattern = r'{\s*"ROLE":[^{]*?"RESPONSE":\s*"[^"]*"[^}]*?}'
    for match in re.finditer(json_pattern, content, re.DOTALL):
        start_pos = match.start()
        json_content = match.group()

        # 清理JSON内容并获取日志行
        cleaned_json, log_lines = clean_json_content(json_content)

        # 处理提取出的日志行
        for log_line in log_lines:
            # 提取玩家消息
            player_msg_match = re.search(
                r'(Player\d+|Moderator)\((\w+)\):\s*(.*?)$', log_line)
            if player_msg_match:
                speaker = player_msg_match.group(1)
                role = player_msg_match.group(2)
                message = player_msg_match.group(3).strip()

                msg_type = "Say"
                if "vote to eliminate" in message:
                    msg_type = "Action"
                elif any(
                        keyword in message for keyword in
                    ["Hunt", "Protect", "Verify", "Poison", "Save", "Pass"]):
                    msg_type = "Action"
                elif speaker == "Moderator":
                    if "choose" in message.lower() or "who" in message.lower():
                        msg_type = "Question"
                    elif "understood" in message.lower():
                        msg_type = "Confirmation"
                    elif "killed" in message.lower(
                    ) or "eliminated" in message.lower():
                        msg_type = "Announcement"
                    else:
                        msg_type = "Instruction"

                messages.append({
                    "timestamp":
                    re.match(timestamp_pattern, log_line).group(1),
                    "position":
                    content.find(log_line),
                    "data": {
                        "speaker": speaker,
                        "content": message,
                        "type": msg_type,
                        "role": role
                    }
                })

        # 处理清理后的JSON
        try:
            data = json.loads(cleaned_json)
            timestamp = next((ts[0] for ts in timestamps if ts[1] < start_pos),
                             None)

            if "THOUGHTS" in data:
                messages.append({
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
                messages.append({
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
            print(f"Failed to parse JSON: {e}")

    # 提取普通消息
    regular_msg_pattern = r'(?:^|\n)(?!{)(Player\d+|Moderator)\(([\w]+)\):\s*(.*?)(?=(?:\n(?:Player\d+|Moderator)\(|\n{|$))'
    for match in re.finditer(regular_msg_pattern, content, re.DOTALL):
        start_pos = match.start()
        timestamp = next((ts[0] for ts in timestamps if ts[1] < start_pos),
                         None)

        speaker = match.group(1)
        role = match.group(2)
        message = match.group(3).strip()

        msg_type = "Say"
        if "vote to eliminate" in message:
            msg_type = "Action"
        elif any(keyword in message for keyword in
                 ["Hunt", "Protect", "Verify", "Poison", "Save", "Pass"]):
            msg_type = "Action"
        elif speaker == "Moderator":
            if "choose" in message.lower() or "who" in message.lower():
                msg_type = "Question"
            elif "understood" in message.lower():
                msg_type = "Confirmation"
            elif "killed" in message.lower() or "eliminated" in message.lower(
            ):
                msg_type = "Announcement"
            else:
                msg_type = "Instruction"

        messages.append({
            "timestamp": timestamp,
            "position": start_pos,
            "data": {
                "speaker": speaker,
                "content": message,
                "type": msg_type,
                "role": role
            }
        })

    # 提取结束
    end_pattern = r"Game over! (.*)"
    end_match = re.search(end_pattern, content)
    if end_match:
        current_round += 1
        answer = end_match.group(1)
        if 'werewolves all dead. The winner is the good guys' in answer:
            for player in players:
                if player["role"] == 'Moderator':
                    continue
                if player["role"] == "Werewolf":
                    player["loss"] += 1
                else:
                    player['win'] += 1
        else:
            for player in players:
                if player["role"] != 'Moderator':
                    continue
                if player["role"] == "Werewolf":
                    player["win"] += 1
                else:
                    player['loss'] += 1

    # 按时间戳和位置排序
    messages.sort(key=lambda x: (x["timestamp"] or "", x["position"]))

    # 提取排序后的对话数据
    dialogue = [msg["data"] for msg in messages]

    # return {"players": players, "dialogue": dialogue}
    return {"players": players, "dialogue": dialogue, "n_rounds": n_rounds, "current_round": current_round}


# 测试代码
def test_parser(filename):
    game_data = parse_log_file(filename)
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
    for msg_type, count in type_count.items():
        print(f"{msg_type}: {count}")

    ipdb.set_trace()
    print("\nSample dialogue entries:")
    for i, entry in enumerate(game_data["dialogue"][:10]):
        print(
            f"{i+1}. [{entry['speaker']}] ({entry['type']}): {entry['content'][:50]}..."
        )


if __name__ == "__main__":
    test_parser(filename="logs/output_1_5.log")
