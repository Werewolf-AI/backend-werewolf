#!/bin/bash

# 接收参数
N_ROUND=$1    # 游戏轮数
N_PLAYER=$2   # 玩家数量
LOG_FILE=$3   # 日志文件路径

# 检查参数
if [ -z "$N_ROUND" ] || [ -z "$N_PLAYER" ] || [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <n_round> <n_player> <log_file>"
    exit 1
fi

# 确保日志文件存在
touch "$LOG_FILE"

# 循环执行指定轮数
for ((i=0; i<=$N_ROUND; i++)); do
    echo -e "\n=== Starting Round $i ===" >> "$LOG_FILE"

    # 执行游戏命令并将输出覆盖到日志文件
    python /home/runner/werewolf/MetaGPT/examples/werewolf_game/start_game.py 20 50 "$N_PLAYER" > "$LOG_FILE" 2>&1

    # 执行游戏命令并将输出覆盖到日志文件同时显示在屏幕上
    # python /home/runner/werewolf/MetaGPT/examples/werewolf_game/start_game.py 20 50 "$N_PLAYER" 2>&1 | tee "$LOG_FILE"

    # 检查上一个命令的执行状态
    if [ $? -eq 0 ]; then
        echo "=== Completed Round $i ===" >> "$LOG_FILE"
    else
        echo "=== Round $i Failed ===" >> "$LOG_FILE"
    fi

    # 可选：在每轮之间添加短暂延时，避免可能的资源竞争
    sleep 1
done

# 在日志末尾添加完成标记
if [ "$success" = true ]; then
    echo -e "\n=== All Rounds Completed ===" >> "$LOG_FILE"
    # 添加短暂延时确保日志被完全写入
    sleep 10
    # 删除日志文件
    rm -f "$LOG_FILE"
else
    echo -e "\n=== Game Failed ===" >> "$LOG_FILE"
fi