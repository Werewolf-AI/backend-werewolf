from flask import Flask, jsonify, request
from flask_cors import CORS
# from parse_log import parse_log_file  # Import your existing parse function
from parse import parse_log_file  # Import your existing parse function
import os
import subprocess
from threading import Lock
import pandas as pd
import ipdb


class GameState:

    def __init__(self):
        self.n_rounds = 10  # 默认值
        self.n_players = 5  # 默认值
        self.log_file = ''
        self.lock = Lock()  # 用于线程安全

    def set(self, n_round, n_players, log_file):
        with self.lock:
            self.n_rounds = n_round
            self.n_players = n_players
            self.log_file = log_file

    def get(self):
        with self.lock:
            return self.n_rounds, self.n_players, self.log_file


app = Flask(__name__)
CORS(app,
     origins=['*'],
     allow_headers=['Content-Type'],
     methods=['GET', 'POST', 'OPTIONS'])

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


@app.route('/api/user-data', methods=['GET', 'POST'])
def upload_user_data():
    try:
        # 处理 GET 请求
        if request.method == 'GET':
            file = '../metagpt/examples/werewolf_game/Users.xlsx'
            df = pd.read_excel(file)
            required_columns = [
                'Username', 'Description', 'Gender', 'Occupation'
            ]

            if not all(col in df.columns for col in required_columns):
                return jsonify({"error": "Missing required columns"}), 400

            usernames = df['Username'].tolist()

            return jsonify({
                'code': 200,
                'message': 'GET request received',
                'usernames': usernames
            }), 200

        # 处理 POST 请求
        if request.method == 'POST':
            # 检查 Content-Type
            if not request.is_json:
                data = request.form  # 尝试获取表单数据
            else:
                data = request.get_json()

            if not data:
                return jsonify({"error": "No data provided"}), 400

            return jsonify({
                'code': 200,
                'message': 'User data uploaded successfully',
            }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to upload user data: {str(e)}"}), 500


@app.route('/api/init-game', methods=['GET', 'POST'])
def init_game():
    try:
        data = None

        # 1. 尝试获取JSON数据
        if request.is_json:
            data = request.get_json()

        # 2. 尝试获取表单数据
        if data is None:
            data = request.form.to_dict()

        # 3. 尝试获取URL参数
        if not data:
            data = request.args.to_dict()

        # 4. 如果所有方法都失败，使用默认值
        if not data:
            data = {}

        n_round = data.get('n_round', 2)
        n_player = data.get('n_player', 5)

        # 使用 os.path.join 构建日志文件路径
        log_dir = os.path.join('./logs')
        log_file = os.path.join(log_dir, f'output_{n_round}_{n_player}.log')
        ensure_file_exists(log_file)

        game_state.set(n_round, n_player, log_file)

        command = f"python ../MetaGPT/examples/werewolf_game/start_game.py {n_round} {n_player} 50 2>&1 | tee {log_file}"

        # 打开已存在的日志文件并追加内容
        # with open(log_file, 'a') as f:
        #     result = subprocess.run(command,
        #                             shell=True,
        #                             capture_output=True,
        #                             text=True)

        #     if result.returncode != 0:
        #         return jsonify({
        #             'code': 500,
        #             'message': "Command execution failed",
        #             'error': result.stderr
        #         }), 500

        return jsonify({
            'code': 200,
            'message': "success",
            'n_round': n_round,
            'n_player': n_player
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "error": str(e),
            "message": "Internal server error"
        }), 500


@app.route('/api/game-data', methods=['GET'])
def get_game_data():
    try:
        n_round, n_player, log_file = game_state.get()
        group_id = n_round
        # group_id = 1
        if group_id == 7:
            group_id = 'final'
        log_file = f'./logs/output_1_11_Group{group_id}.txt'
        names = {
            1: ['Kupo','GaryChia380460','Sczwt','nft2great','nftflair','ggbak',
                'iDominoes','Mirou_Bouguerba','mferPalace','joltikahedron','kenthecaffiend'],  # 11
            2: ['nils116','coswhynotmhm','RuciferX','SpeedyKuma','theblastmax',
                'satsyxbt','DefenseMechanic','aikendrummer','NeonReload','Clmentinho'],  # 10
            3: ['adamagb','0xeightysix','waithustamin109','w4Rd3n','stayhuman456',
                'bowtiedfarmer','IdelPangolin','Cryptking_1','Softboobie','kashcorle','___Resident___'],  # 11
            4: ['Greta_tri','PedakSiri','slowisfast','internatblast','byanonymouscat',
                'Machiavell97647','hydrablast_','Mush_Palace','thedegenius','AIpr0phet','nbwka'],  # 11
            5: ['peterbakker','CarpenterOfWeb3','trumpai007','0xoriok','DuncBlastr',
                'Zoraweb3','elonmusk','NFTeim','starkemind','icobeast','luckynick'],  # 11
            6: ['ETH3','Feik','deb','...CrazyBadger83','lucre_demedici',
                '0xaurelius19980','elonmusk','aciknreth','henloshiba','petobots'],  # 10
            'final': ['GaryChia380460','SpeedyKuma','satsyxbt','___Resident___','PedakSiri',
                      'byanonymouscat','0xoriok','NFTeim','starkemind','Feik', 'aciknreth', 'henloshiba'],  # 12
        }
        # winner: 'SpeedyKuma', 'NFTeim'
        game_data = parse_log_file(log_file, names[group_id])
        return jsonify(game_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=59000)
