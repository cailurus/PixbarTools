#!/bin/sh
# PixDeck 系统监控探针 — 一键安装(Linux)。在【被监控的机器】(如 NAS)上运行:
#
#   curl -fsSL https://raw.githubusercontent.com/cailurus/PixDeck/main/plugins/sysmon/install.sh | sudo sh
#   # 改端口:  ... | sudo PORT=9099 sh
#
# 有 systemd 则装成开机自启服务; 否则用 nohup 后台启动。卸载: sudo systemctl disable --now pixdeck-agent
set -e
PORT="${PORT:-9099}"
RAW="https://raw.githubusercontent.com/cailurus/PixDeck/main/plugins/sysmon/agent.py"
DIR=/opt/pixdeck-agent
PY="$(command -v python3 || command -v python || true)"
[ -n "$PY" ] || { echo "需要 python3(NAS 一般自带, 或在套件中心安装)"; exit 1; }

mkdir -p "$DIR"
curl -fsSL "$RAW" -o "$DIR/agent.py" 2>/dev/null || wget -qO "$DIR/agent.py" "$RAW"

if command -v systemctl >/dev/null 2>&1; then
  cat > /etc/systemd/system/pixdeck-agent.service <<EOF
[Unit]
Description=PixDeck system-stats agent
After=network.target

[Service]
Environment=PORT=$PORT
ExecStart=$PY $DIR/agent.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now pixdeck-agent
  echo "✅ 已装为 systemd 服务 pixdeck-agent,监听 :$PORT(开机自启)"
else
  PORT="$PORT" nohup "$PY" "$DIR/agent.py" >/tmp/pixdeck-agent.log 2>&1 &
  echo "✅ 已后台启动,监听 :$PORT(⚠ 无 systemd,重启后需重跑本脚本)"
fi
echo "现在到 PixDeck 的「系统监控」插件里, 把【远程地址】填成  本机IP:$PORT"
