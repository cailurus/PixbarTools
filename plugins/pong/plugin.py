#!/usr/bin/env python3
"""pong — AI 乒乓球 -> 像素时钟 DIY "pong"（插件, 视觉型）

52×16 上两个 AI 挡板对打一颗球。挡板带轻微反应延迟与误差, 所以会偶尔失球、回合有起伏。
失球后球从中线随机方向重发。整屏用一条 db 位图渲染。

单独运行: python3 plugins/pong/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "pong"
NAME = "乒乓球"
GROUP = "游戏"
DESC = "AI 乒乓球：两个挡板自动对打一颗球，偶尔失球、有来有回。"
DEFAULT_INTERVAL = 1
ITEMS = ["pong"]
W, H = 52, 16
TICK = 0.1
PADH = 4                             # 挡板高
LX, RX = 1, W - 2                    # 左右挡板 x
BALL = 0xFFFFFF
PADDLE = 0x00FF66
BG = 0x000000


def new_game():
    return {"ball": [W / 2, H / 2], "vel": [random.choice([-1, 1]), random.choice([-1, 1])],
            "lp": H / 2 - PADH / 2, "rp": H / 2 - PADH / 2}


def _ai(p, ball_y, approaching):
    """球飞向自己时追球 y, 否则回漂中线(制造来回与偶尔失球)。每 tick 至多 1px。"""
    if approaching:
        target, skip = ball_y, 0.34                        # 偶尔慢半拍 -> 会漏球
    else:
        target, skip = H / 2, 0.4                           # 球离开 -> 回漂中线
    if random.random() < skip:
        return p
    c = p + PADH / 2
    if target > c + 0.5:
        return min(H - PADH, p + 1)
    if target < c - 0.5:
        return max(0, p - 1)
    return p


def _step(g):
    b, v = g["ball"], g["vel"]
    b[0] += v[0]; b[1] += v[1]
    if b[1] <= 0:
        b[1] = 0; v[1] = 1
    elif b[1] >= H - 1:
        b[1] = H - 1; v[1] = -1
    # 左挡板
    if b[0] <= LX + 1 and v[0] < 0:
        if g["lp"] - 1 <= b[1] <= g["lp"] + PADH:
            v[0] = 1; b[0] = LX + 1
        elif b[0] < 0:
            return new_game()                    # 左失球 -> 重发
    # 右挡板
    if b[0] >= RX - 1 and v[0] > 0:
        if g["rp"] - 1 <= b[1] <= g["rp"] + PADH:
            v[0] = -1; b[0] = RX - 1
        elif b[0] > W - 1:
            return new_game()
    g["lp"] = _ai(g["lp"], b[1], v[0] < 0)        # 球向左 = 飞向左挡板
    g["rp"] = _ai(g["rp"], b[1], v[0] > 0)
    return g


def render(g):
    px = [BG] * (W * H)
    for dy in range(PADH):
        px[(int(g["lp"]) + dy) * W + LX] = PADDLE
        px[(int(g["rp"]) + dy) * W + RX] = PADDLE
    bx, by = int(g["ball"][0]), int(g["ball"][1])
    if 0 <= bx < W and 0 <= by < H:
        px[by * W + bx] = BALL
    return core.bitmap_frame(px)


def frame_for(item, interval):
    return render(new_game()), "pong"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    g = new_game()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(g))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  ball={[round(x,1) for x in g['ball']]}")
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
