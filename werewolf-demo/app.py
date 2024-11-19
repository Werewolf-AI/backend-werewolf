from flask import Flask, jsonify, request
from flask_cors import CORS
from parse_log import parse_log_file  # Import your existing parse function
import os
import subprocess
from threading import Lock


class GameState:

    def __init__(self):
        self.n_rounds = 10  # 默认值
        self.n_players = 5  # 默认值
        self.lock = Lock()  # 用于线程安全

    def set(self, n_round, n_players):
        with self.lock:
            self.n_rounds = n_round
            self.n_players = n_players

    def get(self):
        with self.lock:
            return self.n_rounds, self.n_players


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 创建全局游戏状态实例
game_state = GameState()


def ensure_file_exists(file_path):
    """确保文件存在，如果不存在则创建空文件"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
    if not os.path.exists(file_path):
        open(file_path, 'w').close()
    return file_path


@app.route('/api/init-game', methods=['GET', 'POST'])
def init_game():
    try:
        data = request.get_json()
        if data is None:
            # 如果 JSON 数据解析失败，尝试解析表单数据
            data = request.form
        n_round = data.get('n_round', 10)
        n_player = data.get('n_player', 8)

        # 更新当前回合数
        game_state.set(n_round, n_player)

        # 使用 os.path.join 构建日志文件路径
        log_dir = os.path.join('/home/runner/werewolf/werewolf-demo/logs')
        log_file = os.path.join(log_dir, f'output_{n_round}_{n_player}.log')
        ensure_file_exists(log_file)

        # for round_num in range(n_round):
        # 构建命令
        command = [
            'python',
            '/home/runner/werewolf/MetaGPT/examples/werewolf_game/start_game.py',
            '20',
            '3',
            str(n_player),
        ]

        # 打开已存在的日志文件并追加内容
        with open(log_file, 'a') as f:
            # 循环执行n_round次
            for round_num in range(n_round):
                f.write(f"\n=== Starting Round {round_num + 1} ===\n")
                process = subprocess.Popen(command,
                                           stdout=f,
                                           stderr=subprocess.PIPE,
                                           text=True)
                # 等待当前进程完成
                result = process.communicate()

                # 检查进程是否成功完成
                if process.returncode != 0:
                    return jsonify({
                        "error":
                        f"Error in round {round_num + 1}: {result[1]}"
                    }), 500

                f.write(f"=== Completed Round {round_num + 1} ===\n")

        return jsonify({'code': 200, 'message': "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/game-data', methods=['GET'])
def get_game_data():
    try:
        n_round, n_player = game_state.get()

        # Assuming output.log is in the same directory as this script
        game_data = parse_log_file(
            f"/home/runner/werewolf/werewolf-demo/logs/output_{n_round}_{n_player}.log"
        )
        return jsonify(game_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="localhost", debug=True, port=9000)
