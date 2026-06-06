#!/usr/bin/env python3
"""aquarium — 鱼缸 -> 像素时钟 DIY "aquarium"（插件, 视觉型）

几条小鱼(3px 身体 + 朝向尾巴)在缸里游动、到边缘掉头, 底部水草, 偶尔升起气泡。氛围陪伴向。
整屏一条 db 位图渲染。

单独运行: python3 plugins/aquarium/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "aquarium"
NAME = "鱼缸"
GROUP = "视觉"
DESC = "像素小鱼缸：几条小鱼游来游去、吐泡泡，底部有摆动的水草，氛围陪伴向。"
DEFAULT_INTERVAL = 1
ITEMS = ["aquarium"]
W, H = 52, 16
TICK = 0.12
FISH_COLORS = [0xFF6400, 0xFFD000, 0x00E5FF, 0xFF6FB5, 0x00FF66]
WATER_TOP = 0x001530                 # 顶部淡水光(可选)
WEED = 0x0A7A2A                      # 水草 绿
BUBBLE = 0x66CCFF                    # 气泡
BG = 0x000000


def new_tank():
    fish = []
    for _ in range(4):
        fish.append({"x": random.uniform(4, W - 4), "y": random.uniform(2, H - 3),
                     "vx": random.choice([-1, 1]) * random.uniform(0.4, 0.9),
                     "vy": random.uniform(-0.2, 0.2), "c": random.choice(FISH_COLORS)})
    weeds = [(x, random.randint(2, 4)) for x in range(2, W, 6)]   # (底部x, 高)
    return {"fish": fish, "weeds": weeds, "bubbles": [], "t": 0}


def _step(s):
    for f in s["fish"]:
        f["x"] += f["vx"]; f["y"] += f["vy"]
        if f["x"] < 3 or f["x"] > W - 4:
            f["vx"] *= -1; f["x"] = max(3, min(W - 4, f["x"]))
        if f["y"] < 1 or f["y"] > H - 3:
            f["vy"] *= -1; f["y"] = max(1, min(H - 3, f["y"]))
        if random.random() < 0.05:
            f["vy"] = random.uniform(-0.3, 0.3)
    # 气泡上升
    for b in s["bubbles"]:
        b[1] -= 1
    s["bubbles"] = [b for b in s["bubbles"] if b[1] >= 0]
    if random.random() < 0.25:
        s["bubbles"].append([random.randint(2, W - 2), H - 2])
    s["t"] += 1
    return s


def render(s):
    px = [BG] * (W * H)
    # 水草(底部往上)
    for (wx, wh) in s["weeds"]:
        for k in range(wh):
            y = H - 1 - k
            x = wx + (1 if (k % 2 and s["t"] // 4 % 2) else 0)   # 轻微摆动
            if 0 <= x < W and 0 <= y < H:
                px[y * W + x] = WEED
    # 气泡
    for bx, by in s["bubbles"]:
        if 0 <= bx < W and 0 <= by < H:
            px[by * W + bx] = BUBBLE
    # 鱼: 身体3px + 尾巴(朝运动反向)
    for f in s["fish"]:
        x, y = int(f["x"]), int(f["y"])
        d = 1 if f["vx"] >= 0 else -1
        for k in range(3):                       # 身体
            bx = x - d * k
            if 0 <= bx < W and 0 <= y < H:
                px[y * W + bx] = f["c"]
        tx = x - d * 3                            # 尾巴
        if 0 <= tx < W:
            if 0 <= y - 1 < H: px[(y - 1) * W + tx] = f["c"]
            if 0 <= y + 1 < H: px[(y + 1) * W + tx] = f["c"]
    return core.bitmap_frame(px)


def frame_for(item, interval):
    s = new_tank()
    for _ in range(10):
        _step(s)
    return render(s), "aquarium"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    s = new_tank()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(s))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  fish={len(s['fish'])} bubbles={len(s['bubbles'])}")
        _step(s)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
