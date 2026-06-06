#!/usr/bin/env python3
"""pacman — AI 吃豆人 -> 像素时钟 DIY "pacman"（插件, 视觉型）

DFS 生成单宽走廊迷宫(墙蓝), 走廊撒满豆子(暗点)。吃豆人(黄)用 BFS 找最近的豆吃,
两只幽灵(红/青)半追半随机。豆吃光或被幽灵抓到则换一关重来。整屏一条 db 位图。

单独运行: python3 plugins/pacman/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "pacman"
NAME = "吃豆人"
GROUP = "游戏"
DESC = "AI 吃豆人：在自动生成的迷宫里吃光豆子、躲避幽灵，吃完或被抓就换一关。"
DEFAULT_INTERVAL = 1
ITEMS = ["pacman"]
W, H = 52, 16
GW = W - 1 if W % 2 == 0 else W       # 51
GH = H - 1 if H % 2 == 0 else H       # 15
TICK = 0.13
WALL = 0x1030A0                       # 墙 深蓝
PELLET = 0x8A7A30                     # 豆 暗黄(可见, 与墙蓝/黑底区分)
PAC = 0xFFD000                        # 吃豆人 黄
GHOSTC = [0xFF3030, 0x00E5FF]         # 幽灵 红/青
BG = 0x000000
MOVES = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def gen_maze():
    m = [[0] * GW for _ in range(GH)]
    m[0][0] = 1
    stack = [(0, 0)]
    while stack:
        x, y = stack[-1]
        nbrs = [(x + dx, y + dy, dx, dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))
                if 0 <= x + dx < GW and 0 <= y + dy < GH and m[y + dy][x + dx] == 0]
        if nbrs:
            nx, ny, dx, dy = random.choice(nbrs)
            m[y + dy // 2][x + dx // 2] = 1; m[ny][nx] = 1
            stack.append((nx, ny))
        else:
            stack.pop()
    return m


def _cells(m):
    return [(x, y) for y in range(GH) for x in range(GW) if m[y][x]]


def _bfs_step(m, src, is_target):
    """从 src 朝最近满足 is_target 的格走一步, 返回下一格(或原地)。"""
    q = deque([src]); prev = {src: None}
    found = None
    while q:
        cur = q.popleft()
        if is_target(cur):
            found = cur; break
        for dx, dy in MOVES:
            nx, ny = cur[0] + dx, cur[1] + dy
            if 0 <= nx < GW and 0 <= ny < GH and m[ny][nx] and (nx, ny) not in prev:
                prev[(nx, ny)] = cur; q.append((nx, ny))
    if not found or found == src:
        return src
    step = found
    while prev[step] != src:
        step = prev[step]
    return step


def new_level():
    m = gen_maze()
    cells = _cells(m)
    pellets = set(cells)
    pac = (0, 0); pellets.discard(pac)
    far = sorted(cells, key=lambda c: -(abs(c[0] - pac[0]) + abs(c[1] - pac[1])))
    ghosts = [far[0], far[1]]
    return {"m": m, "pellets": pellets, "pac": pac, "ghosts": ghosts}


def _step(s):
    m = s["m"]
    # 吃豆人朝最近豆走一步
    if s["pellets"]:
        s["pac"] = _bfs_step(m, s["pac"], lambda c: c in s["pellets"])
        s["pellets"].discard(s["pac"])
    else:
        return new_level()                       # 吃光 -> 换关
    # 幽灵: 60% 追吃豆人, 40% 随机
    pac = s["pac"]
    ng = []
    for g in s["ghosts"]:
        if random.random() < 0.6:
            ng.append(_bfs_step(m, g, lambda c: c == pac))
        else:
            opts = [(g[0] + dx, g[1] + dy) for dx, dy in MOVES
                    if 0 <= g[0] + dx < GW and 0 <= g[1] + dy < GH and m[g[1] + dy][g[0] + dx]]
            ng.append(random.choice(opts) if opts else g)
    s["ghosts"] = ng
    if pac in s["ghosts"]:                        # 被抓 -> 换关
        return new_level()
    return s


def render(s):
    m = s["m"]
    px = [BG] * (W * H)
    for y in range(GH):
        for x in range(GW):
            if not m[y][x]:
                px[y * W + x] = WALL
    for (x, y) in s["pellets"]:
        px[y * W + x] = PELLET
    for i, (gx, gy) in enumerate(s["ghosts"]):
        px[gy * W + gx] = GHOSTC[i % len(GHOSTC)]
    pacx, pacy = s["pac"]
    px[pacy * W + pacx] = PAC
    return core.bitmap_frame(px)


def frame_for(item, interval):
    s = new_level()
    for _ in range(30):
        s = _step(s)
    return render(s), "pacman"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    s = new_level()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(s))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  pellets={len(s['pellets'])}")
        s = _step(s)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
