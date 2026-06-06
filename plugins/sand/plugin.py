#!/usr/bin/env python3
"""sand — 落沙 -> 像素时钟 DIY "sand"（插件, 视觉型）

顶部不断落下彩色沙粒, 受"重力"下落、堆积成丘, 堆满则清空重来(解压向)。
经典 falling-sand 元胞规则: 沙粒下方为空则落, 否则尝试斜下滑。整屏一条 db 位图渲染。

单独运行: python3 plugins/sand/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "sand"
NAME = "落沙"
GROUP = "视觉"
DESC = "落沙：顶部不断落下彩色沙粒，受重力堆积成丘，堆满后自动重来。"
DEFAULT_INTERVAL = 1
ITEMS = ["sand"]
W, H = 52, 16
TICK = 0.08
COLORS = [0xFFD000, 0xFF6400, 0xFF3030, 0x00E5FF, 0x00FF66, 0xFF6FB5]
BG = 0x000000
SPAWN = 3                            # 每帧顶部新增沙粒数


def new_grid():
    return [[0] * W for _ in range(H)]


def _step(g):
    # 重力: 自底向上扫, 每粒尝试 下 / 斜下落
    for y in range(H - 2, -1, -1):
        order = list(range(W))
        random.shuffle(order)                    # 随机左右倾向, 更自然
        for x in order:
            c = g[y][x]
            if not c:
                continue
            if g[y + 1][x] == 0:
                g[y + 1][x] = c; g[y][x] = 0
            else:
                dirs = [-1, 1]; random.shuffle(dirs)
                for dx in dirs:
                    nx = x + dx
                    if 0 <= nx < W and g[y + 1][nx] == 0:
                        g[y + 1][nx] = c; g[y][x] = 0
                        break
    # 顶部撒新沙
    full_top = sum(1 for x in range(W) if g[0][x]) > W * 0.6
    if full_top:
        return new_grid()                        # 堆满 -> 清空重来
    for _ in range(SPAWN):
        x = random.randrange(W)
        if g[0][x] == 0:
            g[0][x] = random.choice(COLORS)
    return g


def render(g):
    px = [BG] * (W * H)
    for y in range(H):
        row = g[y]
        for x in range(W):
            if row[x]:
                px[y * W + x] = row[x]
    return core.bitmap_frame(px)


def frame_for(item, interval):
    g = new_grid()
    for _ in range(40):
        g = _step(g)
    return render(g), "sand"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    g = new_grid()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(g))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  grains={sum(1 for r in g for c in r if c)}")
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
