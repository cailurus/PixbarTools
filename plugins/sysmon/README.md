# 系统监控插件 — 本机 & 远程(NAS / 局域网机器)

「系统监控」(`sysmon`)默认监控**运行 PixDeck 的这台电脑**。它也能监控**局域网内另一台机器**(比如你家的 NAS):只要在那台机器上跑一个超轻量探针 `agent.py`,然后在插件的**「远程地址」**选项里填上它的 `IP:端口` 即可。

```
你的电脑 ── PixDeck ── 像素时钟              NAS ── agent.py(:9099)
                │                              ▲
                └──────── 抓 http://NAS:9099 ──┘
```

探针只暴露 CPU / 内存 / 磁盘 / GPU 的**百分比**(纯标准库、无需密码、无需 root)。

---

## 一、在被监控的机器上装探针(三选一,挑最顺手的)

### 方式 A — Docker(NAS 最省事,推荐)

无需下载文件、无需构建镜像,一行搞定(容器启动时自动拉取探针):

```bash
docker run -d --name pixdeck-agent --restart unless-stopped \
  --pid=host -p 9099:9099 -v /:/host:ro -e STATS_PATH=/host python:3-alpine \
  sh -c "wget -qO /agent.py https://raw.githubusercontent.com/cailurus/PixDeck/main/plugins/sysmon/agent.py && python3 /agent.py"
```

> `--pid=host` 让 CPU/内存反映宿主;`-v /:/host:ro -e STATS_PATH=/host` 让磁盘反映宿主根分区。
> 群晖 Container Manager / 威联通 Container Station 也可以照这些参数在图形界面里建容器。
> 想用本仓库的 `Dockerfile` 自建镜像也行:`docker build -t pixdeck-agent plugins/sysmon`。

### 方式 B — 一键脚本(Linux + systemd)

在被监控机器上以 root 运行,装成开机自启的服务:

```bash
curl -fsSL https://raw.githubusercontent.com/cailurus/PixDeck/main/plugins/sysmon/install.sh | sudo sh
# 改端口:  ... | sudo PORT=9099 sh
```

### 方式 C — 手动(任何有 Python3 的机器)

```bash
curl -fsSLO https://raw.githubusercontent.com/cailurus/PixDeck/main/plugins/sysmon/agent.py
python3 agent.py          # 默认 0.0.0.0:9099, 磁盘看 /
# 自定义:  PORT=9099 STATS_PATH=/ python3 agent.py
```

装好后,在那台机器上验证一下:`curl http://localhost:9099` 应返回类似
`{"host":"nas","cpu":12,"ram":63,"dsk":48,"gpu":null}`。

---

## 二、在 PixDeck 里指向它

打开「系统监控」插件 → **「远程地址」** 填 **`NAS的IP:9099`**(端口默认 9099 可省略)→ 保存。
留空则恢复监控本机。柱状图 / CPU 走势图两种显示照常可切。

---

## 说明

- 探针主要面向 **Linux**(CPU/内存读 `/proc`)。磁盘用 `statvfs`,各平台通用;GPU 仅在有 `nvidia-smi` 时可读,多数 NAS 为 `null`(插件会跳过 GPU 项)。
- 探针在局域网内**无鉴权**地暴露这几个百分比(低敏感度)。请只在可信局域网内使用,不要把 9099 端口暴露到公网。
- 探针进程极轻(纯标准库的 `http.server`),常驻几乎不占资源。
