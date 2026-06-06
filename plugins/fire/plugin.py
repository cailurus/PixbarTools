#!/usr/bin/env python3
"""fire — 火焰 -> 像素时钟 DIY "fire"（插件, 视觉型）

经典 demoscene 火焰: 底部不断生热, 每格热量向上扩散并衰减, 热度经火焰调色板(黑->红->橙->黄->白)上色。
整屏一条 db 位图渲染。

单独运行: python3 plugins/fire/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "fire"
NAME = "火焰"
GROUP = "视觉"
DESC = "经典火焰特效：屏幕底部不断生热、向上燃烧跳动的 demoscene 火焰。"
DEFAULT_INTERVAL = 1
ITEMS = ["fire"]
W, H = 52, 16
TICK = 0.08


def _palette():
    """0..36 热度 -> 颜色(黑->暗红->红->橙->黄->白)。"""
    stops = [(0, (0, 0, 0)), (6, (60, 0, 0)), (12, (180, 30, 0)),
             (20, (255, 100, 0)), (28, (255, 200, 30)), (36, (255, 255, 220))]
    pal = []
    for i in range(37):
        for k in range(len(stops) - 1):
            a, ca = stops[k]; b, cb = stops[k + 1]
            if a <= i <= b:
                t = (i - a) / (b - a)
                r = int(ca[0] + (cb[0] - ca[0]) * t)
                gg = int(ca[1] + (cb[1] - ca[1]) * t)
                bl = int(ca[2] + (cb[2] - ca[2]) * t)
                pal.append((r << 16) | (gg << 8) | bl)
                break
    return pal


PAL = _palette()
HMAX = 36


def new_heat():
    return [[0] * W for _ in range(H)]


def _step(heat):
    for x in range(W):                            # 底部生热(随机, 偶有冷点制造火舌)
        heat[H - 1][x] = 0 if random.random() < 0.18 else HMAX
    for y in range(H - 1):                         # 向上扩散+衰减
        for x in range(W):
            below = heat[y + 1][x]
            l = heat[y + 1][(x - 1) % W]
            r = heat[y + 1][(x + 1) % W]
            avg = (below * 2 + l + r) // 4
            heat[y][x] = max(0, avg - random.randint(1, 3))
    return heat


def render(heat):
    px = [0] * (W * H)
    for y in range(H):
        for x in range(W):
            px[y * W + x] = PAL[min(HMAX, heat[y][x])]
    return core.bitmap_frame(px)


def frame_for(item, interval):
    h = new_heat()
    for _ in range(20):
        _step(h)
    return render(h), "fire"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    heat = new_heat()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(heat))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  fire")
        _step(heat)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
