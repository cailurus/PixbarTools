#!/usr/bin/env python3
"""PixDeck 系统监控探针 — 在被监控的机器(NAS / 服务器 / 另一台电脑)上运行。

在一个 HTTP 端口上吐出本机 CPU / 内存 / 磁盘 / GPU 占用的 JSON;PixDeck 的「系统监控」插件
填上这台机器的 `IP:端口` 即可远程监控它。纯 Python 标准库, 零依赖, 主要面向 Linux(读 /proc)。

  python3 agent.py                          # 默认 0.0.0.0:9099, 磁盘看根分区 /
  PORT=9099 STATS_PATH=/ python3 agent.py   # 用环境变量改端口 / 磁盘路径

返回示例: {"host":"nas","cpu":12,"ram":63,"dsk":48,"gpu":null}  (百分比 0-100, 取不到为 null)
"""
import json, os, socket, subprocess, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "9099"))
STATS_PATH = os.environ.get("STATS_PATH", "/")


def cpu_percent():
    """Linux: 两次读 /proc/stat 求繁忙占比(扣掉 idle+iowait)。非 Linux 返回 None。"""
    try:
        def read():
            with open("/proc/stat") as f:
                v = list(map(int, f.readline().split()[1:]))
            idle = v[3] + (v[4] if len(v) > 4 else 0)        # idle + iowait
            return sum(v), idle
        t1, i1 = read(); time.sleep(0.25); t2, i2 = read()
        dt, di = t2 - t1, i2 - i1
        return int(round(100 * (dt - di) / dt)) if dt > 0 else None
    except Exception:
        return None


def mem_percent():
    """Linux: /proc/meminfo 算已用 = (MemTotal - MemAvailable) / MemTotal。"""
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, _, rest = line.partition(":")
                info[k] = int(rest.split()[0])               # kB
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", info.get("MemFree", 0))
        return int(round(100 * (total - avail) / total)) if total else None
    except Exception:
        return None


def disk_percent():
    """STATS_PATH 所在文件系统已用占比(statvfs, Linux/mac 通用)。"""
    try:
        s = os.statvfs(STATS_PATH)
        total = s.f_blocks * s.f_frsize
        free = s.f_bavail * s.f_frsize
        return int(round(100 * (total - free) / total)) if total else None
    except Exception:
        return None


def gpu_percent():
    """有 NVIDIA 卡则用 nvidia-smi, 否则 None(多数 NAS 无 GPU)。"""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu",
                              "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=3).stdout
        return int(out.strip().splitlines()[0])
    except Exception:
        return None


def stats():
    return {"host": socket.gethostname(), "cpu": cpu_percent(),
            "ram": mem_percent(), "dsk": disk_percent(), "gpu": gpu_percent()}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(stats()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"PixDeck agent -> 0.0.0.0:{PORT}  (disk={STATS_PATH}, host={socket.gethostname()})")
    try:
        ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
