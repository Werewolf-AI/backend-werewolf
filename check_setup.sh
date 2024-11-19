#!/bin/bash

# 创建日志目录
mkdir -p /home/runner/werewolf/werewolf-demo/logs
chmod 777 /home/runner/werewolf/werewolf-demo/logs

# 检查Flask服务
echo "Checking Flask service..."
curl -v http://localhost:9000/api/game-data?n_round=1 2>&1

# 检查React服务
echo -e "\nChecking React service..."
curl -v http://localhost:3000 2>&1

# 检查日志目录权限
echo -e "\nChecking logs directory..."
ls -la /home/runner/werewolf/werewolf-demo/logs

# 检查进程
echo -e "\nChecking running processes..."
ps aux | grep python
ps aux | grep node