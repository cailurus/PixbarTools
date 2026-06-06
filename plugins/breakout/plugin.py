#!/usr/bin/env python3
"""breakout — AI 打砖块 -> 像素时钟 DIY "breakout"（插件, 视觉型）

52×16 上 AI 挡板接球、把顶部三排砖清光。砖按行染色(红/黄/绿)。清光或失球则重置。
整屏用一条 db 位图渲染。

单独运行: python3 plugins/breakout/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "breakout"
NAME = "打砖块"
GROUP = "游戏"
DESC = "AI 打砖块：挡板自动接球，把顶部三排彩色砖块逐个清光，清完重来。"
DEFAULT_INTERVAL = 1
ITEMS = ["breakout"]
W, H = 52, 16
TICK = 0.1
BW = 4                               # 砖宽
ROWS = [1, 2, 3]                     # 砖所在行
ROW_COLOR = {1: 0xFF3030, 2: 0xFFD000, 3: 0x00FF66}
PADY = H - 1                         # 挡板行
PADW = 7
PADDLE = 0xFFFFFF
BALL = 0x00E5FF
BG = 0x000000


def new_bricks():
    cols = W // BW
    return {(r, c) for r in ROWS for c in range(cols)}


def new_game():
    return {"bricks": new_bricks(),
            "ball": [W / 2, H - 3], "vel": [random.choice([-1, 1]), -1],
            "pad": W / 2 - PADW / 2}


def _brick_at(bricks, x, y):
    if y in ROWS:
        c = x // BW
        if (y, c) in bricks:
            return (y, c)
    return None


def _step(g):
    b, v = g["ball"], g["vel"]
    nx, ny = b[0] + v[0], b[1] + v[1]
    if nx <= 0:
        nx = 0; v[0] = 1
    elif nx >= W - 1:
        nx = W - 1; v[0] = -1
    if ny <= 0:
        ny = 0; v[1] = 1
    hit = _brick_at(g["bricks"], int(nx), int(ny))    # 撞砖
    if hit:
        g["bricks"].discard(hit); v[1] = -v[1]; ny = b[1]
    if int(ny) >= PADY - 1 and v[1] > 0:              # 挡板接球
        if g["pad"] - 1 <= nx <= g["pad"] + PADW:
            v[1] = -1; ny = PADY - 2
        elif ny >= H:
            return new_game()                         # 漏球 -> 重置
    b[0], b[1] = nx, ny
    # AI 挡板朝球 x 追(每 tick 至多 2px)
    c = g["pad"] + PADW / 2
    if b[0] > c + 0.5:
        g["pad"] = min(W - PADW, g["pad"] + 2)
    elif b[0] < c - 0.5:
        g["pad"] = max(0, g["pad"] - 2)
    if not g["bricks"]:                               # 清光 -> 重置
        return new_game()
    return g


def render(g):
    px = [BG] * (W * H)
    for (r, c) in g["bricks"]:
        for dx in range(BW - 1):                      # 砖间留 1px 缝
            px[r * W + c * BW + dx] = ROW_COLOR[r]
    for dx in range(PADW):
        x = int(g["pad"]) + dx
        if 0 <= x < W:
            px[PADY * W + x] = PADDLE
    bx, by = int(g["ball"][0]), int(g["ball"][1])
    if 0 <= bx < W and 0 <= by < H:
        px[by * W + bx] = BALL
    return core.bitmap_frame(px)


def frame_for(item, interval):
    return render(new_game()), "breakout"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    g = new_game()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(g))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  bricks={len(g['bricks'])} ball={[round(x,1) for x in g['ball']]}")
        g = _step(g)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
