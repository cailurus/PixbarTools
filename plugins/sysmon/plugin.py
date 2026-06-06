#!/usr/bin/env python3
"""sysmon — 本机系统监控 -> 像素时钟 DIY "sysmon"（插件, macOS）

两种显示(面板"显示"下拉可实时切换):
  bar   — 全屏轮播 CPU/RAM/GPU/DSK: 白标签 + 染色数值(右对齐) + 右侧 7x10 负载柱。
  chart — CPU 走势图: 左侧染色数值 + 右侧 draw 折线(最近 ~30 个采样, 每 tick 滚动)。
颜色按负载: <50 绿 / <80 黄 / >=80 红。数据源(免 sudo): top / vm_stat / ioreg / df。

单独运行: python3 plugins/sysmon/plugin.py [--device IP] [--interval 5] [--dry-run] [--once]
"""
import os, sys, re, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "sysmon"
NAME = "系统监控"
GROUP = "信息"
DESC = "系统监控：本机 CPU / 内存 / GPU / 磁盘占用，可选柱状图或 CPU 走势图两种显示。"
DEFAULT_INTERVAL = 5
ITEMS = ["CPU", "RAM", "GPU", "DSK"]
WHITE = "#FFFFFF"
OPTIONS = [{
    "key": "display", "label": "显示", "default": "bar",
    "choices": [["bar", "柱子(轮播全部)"], ["chart", "CPU 走势图"]],
}]


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=15).stdout


def get_cpu():
    try:
        line = [l for l in sh(["top", "-l", "2", "-n", "0"]).splitlines() if "CPU usage" in l][-1]
        return int(round(100 - float(re.search(r"([\d.]+)%\s*idle", line).group(1))))
    except Exception:
        return None


def get_ram():
    try:
        total = int(sh(["sysctl", "-n", "hw.memsize"]))
        vm = sh(["vm_stat"])
        psize = int(re.search(r"page size of (\d+) bytes", vm).group(1))
        def pages(label):
            m = re.search(label + r":\s+(\d+)\.", vm)
            return int(m.group(1)) if m else 0
        used = (pages("Pages active") + pages("Pages wired down")
                + pages("Pages occupied by compressor")) * psize
        return int(round(used / total * 100))
    except Exception:
        return None


def get_gpu():
    try:
        out = sh(["ioreg", "-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"])
        return int(re.search(r'"Device Utilization %"=(\d+)', out).group(1))
    except Exception:
        return None


def get_dsk():
    try:
        return int(re.search(r"(\d+)%", sh(["df", "-k", "/"]).splitlines()[-1]).group(1))
    except Exception:
        return None


GETTERS = {"CPU": get_cpu, "RAM": get_ram, "GPU": get_gpu, "DSK": get_dsk}


def load_color(p):
    return "#00FF66" if p < 50 else "#FFD000" if p < 80 else "#FF3030"


def frame_for(label, interval):
    v = GETTERS[label]()
    if v is None:
        return None
    color = load_color(v)
    bx, by, bw, bh = 43, 3, 7, 10
    fill = int(round(max(0, min(100, v)) / 100 * bh))
    if v > 0 and fill < 1:
        fill = 1
    frame = {
        "duration": interval,
        "text": [
            {"content": label, "fontHeight": 10, "x": 2, "y": 3, "color": WHITE},
            {"content": str(v), "fontHeight": 10, "x": -1000, "y": 3,
             "align": "right", "rect": [0, 0, 41, 16], "color": color},
        ],
        "draw": [
            {"dr": [bx, by, bw, bh, color]},
            {"df": [bx, by + (bh - fill), bw, fill, color]},
        ],
    }
    return frame, f"{label:4} {v:3d}%  {color}"


# ---- CPU 走势图 ----
CHART_DIV = 21                       # 分隔竖线 x(左侧给 "CPU" 标签留位)
CHART_X0, CHART_X1 = 23, 51          # 折线区横向范围(29 列 = 29 采样)
CHART_N = CHART_X1 - CHART_X0 + 1


def _ymap(v):
    return max(0, min(15, 15 - round(max(0, min(100, v)) / 100 * 15)))


def chart_frame(hist, interval):
    """hist=最近 CPU 采样列表(末尾最新)。左 "CPU" 标签(按负载染色) + 右折线。draw <=32 条。"""
    v = hist[-1]
    color = load_color(v)
    draw = [{"dl": [CHART_DIV, 0, CHART_DIV, 15, "#333333"]}]   # 分隔线
    pts = hist[-CHART_N:]
    n = len(pts)
    if n == 1:
        draw.append({"dp": [CHART_X0, _ymap(pts[0]), color]})
    else:
        for k in range(n - 1):
            draw.append({"dl": [CHART_X0 + k, _ymap(pts[k]),
                                CHART_X0 + k + 1, _ymap(pts[k + 1]), color]})
    frame = {
        "duration": interval,
        "text": [{"content": "CPU", "fontHeight": 10, "x": 1, "y": 3,
                  "color": color, "rect": [0, 0, CHART_DIV, 16]}],
        "draw": draw,
    }
    return frame, f"CPU chart {v:3d}%  (n={n})"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """display=bar: 轮播 CPU/RAM/GPU/DSK 柱; display=chart: CPU 走势图滚动。选项可热切换。"""
    options = options or {}
    i = 0
    hist = []
    while stop is None or not stop.is_set():
        ts = time.strftime("%H:%M:%S")
        if options.get("display", "bar") == "chart":
            v = get_cpu()
            if v is None:
                log("  read fail: CPU")
            else:
                hist.append(v); del hist[:-CHART_N]
                frame, line = chart_frame(hist, interval)
                if dry_run:
                    log(f"{ts}  {line}")
                else:
                    try:
                        core.push(device, APP, frame); log(f"{ts}  {line}")
                    except Exception as e:
                        log(f"  push fail: {e}")
        else:
            label = ITEMS[i % len(ITEMS)]; i += 1
            res = frame_for(label, interval)
            if res:
                frame, line = res
                if dry_run:
                    log(f"{ts}  {line}")
                else:
                    try:
                        core.push(device, APP, frame); log(f"{ts}  {line}")
                    except Exception as e:
                        log(f"  push fail: {e}")
            else:
                log(f"  read fail: {label}")
        if once:
            break
        if stop is not None:
            if stop.wait(interval):
                break
        else:
            time.sleep(interval)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
