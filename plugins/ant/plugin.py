#!/usr/bin/env python3
"""ant — 兰顿蚂蚁 -> 像素时钟 DIY "ant"（插件, 视觉型）

兰顿蚂蚁: 一只蚂蚁按两条简单规则爬行——白格上右转、黑格上左转, 经过即翻转该格颜色。
简单规则却涌现出对称图案与"高速公路"。约 2000 步或蚂蚁久未离开区域则重置。整屏一条 db 位图。

单独运行: python3 plugins/ant/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "ant"
NAME = "兰顿蚂蚁"
GROUP = "视觉"
DESC = "兰顿蚂蚁元胞自动机：一只蚂蚁按两条简单规则爬行，却会逐渐演化出对称图案与“高速公路”。"
DEFAULT_INTERVAL = 1
ITEMS = ["ant"]
W, H = 52, 16
TICK = 0.05
STEPS_PER_FRAME = 3                  # 每帧推进几步(太慢看不出)
RESET_AFTER = 2200
TRAIL = 0x00FF66                     # 翻转过的格(绿)
ANTC = 0xFF3030                      # 蚂蚁(红)
BG = 0x000000
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0)]   # 上右下左


def new_state():
    return {"grid": [[0] * W for _ in range(H)], "x": W // 2, "y": H // 2, "d": 0, "n": 0}


def _step(s):
    g = s["grid"]
    if g[s["y"]][s["x"]]:                      # 白格 -> 右转, 翻黑
        s["d"] = (s["d"] + 1) % 4; g[s["y"]][s["x"]] = 0
    else:                                      # 黑格 -> 左转, 翻白
        s["d"] = (s["d"] - 1) % 4; g[s["y"]][s["x"]] = 1
    dx, dy = DIRS[s["d"]]
    s["x"] = (s["x"] + dx) % W                 # 环形边界
    s["y"] = (s["y"] + dy) % H
    s["n"] += 1


def render(s):
    px = [BG] * (W * H)
    for y in range(H):
        row = s["grid"][y]
        for x in range(W):
            if row[x]:
                px[y * W + x] = TRAIL
    px[s["y"] * W + s["x"]] = ANTC
    return core.bitmap_frame(px)


def frame_for(item, interval):
    s = new_state()
    for _ in range(300):
        _step(s)
    return render(s), "ant"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    s = new_state()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(s))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  steps={s['n']}")
        for _ in range(STEPS_PER_FRAME):
            _step(s)
        if s["n"] >= RESET_AFTER:
            s = new_state()
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
