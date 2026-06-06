#!/usr/bin/env python3
"""snake — AI 贪吃蛇 -> 像素时钟 DIY "snake"（插件）

52×16 上一条自动寻路的蛇: 贪心朝食物移动并避免撞墙/撞身, 吃到食物长大, 走投无路则重开。
(自定义 App 协议是"只推送、收不到设备按键", 故为观赏用 AI 蛇, 非手动操控。)
蛇头白、蛇身绿、食物红; 整屏用一条 `db` 位图指令渲染(像素值十进制 0x00RRGGBB)。

单独运行: python3 plugins/snake/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "snake"
NAME = "贪吃蛇"
GROUP = "游戏"
DESC = "AI 贪吃蛇：自动寻路找食物、吃到就长大，撞墙或撞到自己则重开。"
DEFAULT_INTERVAL = 1
ITEMS = ["snake"]
W, H = 52, 16
TICK = 0.18                          # 移动节奏(与面板 interval 解耦)
HEAD = 0xFFFFFF                      # 蛇头 白
BODY = 0x00FF66                      # 蛇身 绿
FOOD = 0xFF3030                      # 食物 红
DEAD = 0x000000
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def new_game():
    snake = [(W // 2, H // 2), (W // 2 - 1, H // 2), (W // 2 - 2, H // 2)]
    return {"snake": snake, "dir": (1, 0), "food": _spawn(snake)}


def _spawn(snake):
    body = set(snake)
    free = [(x, y) for y in range(H) for x in range(W) if (x, y) not in body]
    return random.choice(free) if free else None


def _choose(game):
    """贪心: 在不撞墙/不撞身(蛇尾即将让位除外)的方向里, 选最靠近食物的。无安全方向则返回 None。"""
    hx, hy = game["snake"][0]
    fx, fy = game["food"]
    occupied = set(game["snake"][:-1])           # 蛇尾下一步会移开
    cur = game["dir"]
    cands = []
    for dx, dy in DIRS:
        if (dx, dy) == (-cur[0], -cur[1]):       # 不能直接掉头
            continue
        nx, ny = hx + dx, hy + dy
        if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in occupied:
            cands.append((abs(nx - fx) + abs(ny - fy), (dx, dy)))
    if not cands:
        return None
    cands.sort()
    return cands[0][1]


def _step(game):
    """前进一步; 返回 True 表示存活, False 表示死亡(需重开)。"""
    d = _choose(game)
    if d is None:
        return False
    game["dir"] = d
    hx, hy = game["snake"][0]
    head = (hx + d[0], hy + d[1])
    if head == game["food"]:
        game["snake"].insert(0, head)            # 吃到 -> 长大
        game["food"] = _spawn(game["snake"])
        if game["food"] is None:                 # 填满 -> 通关重开
            return False
    else:
        game["snake"].insert(0, head)
        game["snake"].pop()                      # 普通前进 -> 尾巴跟进
    return True


def render(game):
    px = [DEAD] * (W * H)
    for i, (x, y) in enumerate(game["snake"]):
        px[y * W + x] = HEAD if i == 0 else BODY
    if game["food"]:
        fx, fy = game["food"]
        px[fy * W + fx] = FOOD
    return {"duration": 5, "draw": [{"db": [0, 0, W, H, px]}]}, len(game["snake"])


def frame_for(item, interval):
    g = new_game()
    frame, ln = render(g)
    return frame, f"snake len={ln}"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """AI 蛇循环: 每 TICK 前进一步; 死亡/通关则重开。"""
    g = new_game()
    while stop is None or not stop.is_set():
        frame, ln = render(g)
        if not dry_run:
            try: core.push(device, APP, frame)
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  len={ln} head={g['snake'][0]} food={g['food']}")
        if not _step(g):                          # 死亡/通关 -> 重开
            log(f"{time.strftime('%H:%M:%S')}  restart (len was {ln})")
            g = new_game()
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
