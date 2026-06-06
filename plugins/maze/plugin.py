#!/usr/bin/env python3
"""maze — 走迷宫 -> 像素时钟 DIY "maze"（插件, 视觉型）

先用 DFS 生成一座迷宫(墙蓝), 再一个亮点从左上 BFS 最短路走到右下(走过留淡绿、当前点黄)。
走到终点后停留片刻, 重新生成。整屏一条 db 位图。

单独运行: python3 plugins/maze/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
from collections import deque
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "maze"
NAME = "走迷宫"
GROUP = "视觉"
DESC = "走迷宫：自动生成一座迷宫，再用一个亮点从左上角寻路走到右下角。"
DEFAULT_INTERVAL = 1
ITEMS = ["maze"]
W, H = 52, 16                        # 显示尺寸
# 迷宫单元网格(奇数尺寸: 单元+墙), 取能放进 52x16 的最大奇数
GW = W if W % 2 else W - 1           # 51
GH = H if H % 2 else H - 1           # 15
WALL = 0x1E5AFF                      # 墙 蓝
PATH_DONE = 0x0A4020                 # 走过 淡绿
CUR = 0xFFD000                       # 当前 黄
GOAL = 0xFF3030                      # 终点 红
BG = 0x000000


def gen_maze():
    """DFS 生成: m[y][x]=1 通路 0 墙。单元在偶数坐标。"""
    m = [[0] * GW for _ in range(GH)]
    sx, sy = 0, 0
    m[0][0] = 1
    stack = [(0, 0)]
    while stack:
        x, y = stack[-1]
        nbrs = []
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GW and 0 <= ny < GH and m[ny][nx] == 0:
                nbrs.append((nx, ny, dx, dy))
        if nbrs:
            nx, ny, dx, dy = random.choice(nbrs)
            m[y + dy // 2][x + dx // 2] = 1
            m[ny][nx] = 1
            stack.append((nx, ny))
        else:
            stack.pop()
    return m


def solve(m):
    """BFS 从 (0,0) 到 (GW-1,GH-1) 的最短路点列。"""
    goal = (GW - 1, GH - 1)
    q = deque([(0, 0)]); prev = {(0, 0): None}
    while q:
        x, y = q.popleft()
        if (x, y) == goal:
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < GW and 0 <= ny < GH and m[ny][nx] and (nx, ny) not in prev:
                prev[(nx, ny)] = (x, y); q.append((nx, ny))
    path = []
    cur = goal if goal in prev else None
    while cur:
        path.append(cur); cur = prev[cur]
    path.reverse()
    return path


def new_state():
    m = gen_maze()
    return {"m": m, "path": solve(m), "i": 0, "hold": 0}


def render(s):
    m, path, i = s["m"], s["path"], s["i"]
    px = [BG] * (W * H)
    for y in range(GH):
        for x in range(GW):
            px[y * W + x] = BG if m[y][x] else WALL
    for p in path[:i]:                          # 已走过
        px[p[1] * W + p[0]] = PATH_DONE
    if path:
        gx, gy = path[-1]; px[gy * W + gx] = GOAL
        cx, cy = path[min(i, len(path) - 1)]
        px[cy * W + cx] = CUR
    return core.bitmap_frame(px)


def frame_for(item, interval):
    s = new_state(); s["i"] = len(s["path"]) // 2
    return render(s), "maze"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    s = new_state()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(s))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  i={s['i']}/{len(s['path'])}")
        if s["i"] < len(s["path"]):
            s["i"] += 1
        else:
            s["hold"] += 1
            if s["hold"] > 12:                  # 到终点停留后重生
                s = new_state()
        if once:
            break
        if stop is not None:
            if stop.wait(0.12):
                break
        else:
            time.sleep(0.12)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
