# PixDeck 系统监控探针 — 在被监控机器(NAS / 服务器)上跑, 暴露 CPU/内存/磁盘/GPU JSON。
# 构建: docker build -t pixdeck-agent plugins/sysmon
# 运行: docker run -d --name pixdeck-agent --restart unless-stopped \
#         --pid=host -p 9099:9099 -v /:/host:ro -e STATS_PATH=/host pixdeck-agent
#   --pid=host + /proc 让 CPU/内存反映宿主; -v /:/host:ro + STATS_PATH=/host 让磁盘反映宿主根分区。
FROM python:3-alpine
COPY agent.py /agent.py
EXPOSE 9099
ENTRYPOINT ["python3", "/agent.py"]
