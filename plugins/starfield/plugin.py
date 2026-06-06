#!/usr/bin/env python3
"""starfield — 星空穿梭 -> 像素时钟 DIY "starfield"（插件, 视觉型）

从屏幕中心向外飞出的星点(曲速感): 近的星更快更亮(白), 远的慢而暗(灰)。飞出屏外则在中心重生。
整屏用一条 db 位图渲染。

单独运行: python3 plugins/starfield/plugin.py [--device IP] [--dry-run] [--once]
"""
import math, os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "starfield"
NAME = "星空穿梭"
GROUP = "视觉"
DESC = "星空穿梭：星点从屏幕中心向外飞出，营造曲速前进的穿梭感。"
DEFAULT_INTERVAL = 1
ITEMS = ["starfield"]
W, H = 52, 16
TICK = 0.08
NSTARS = 40
CX, CY = W / 2, H / 2
BG = 0x000000


def _shade(z):
    """z: 0(远)->1(近) 映射灰->白。"""
    v = int(80 + 175 * z)
    return (v << 16) | (v << 8) | v


def _new_star():
    a = random.uniform(0, 6.2832)
    return {"a": a, "r": random.uniform(1, 3), "spd": random.uniform(0.15, 0.6)}


def new_field():
    return [_new_star() for _ in range(NSTARS)]


def _step(stars):
    for s in stars:
        s["r"] += s["spd"] * (0.5 + s["r"] * 0.25)     # 越往外越快(加速感)
        x = CX + s["r"] * math.cos(s["a"])
        y = CY + s["r"] * math.sin(s["a"])
        if x < 0 or x >= W or y < 0 or y >= H:
            s.update(_new_star())                       # 飞出 -> 中心重生
    return stars


def render(stars):
    px = [BG] * (W * H)
    for s in stars:
        x = int(CX + s["r"] * math.cos(s["a"]))
        y = int(CY + s["r"] * math.sin(s["a"]))
        if 0 <= x < W and 0 <= y < H:
            z = min(1.0, s["r"] / (W / 2))
            px[y * W + x] = _shade(z)
    return core.bitmap_frame(px)


def frame_for(item, interval):
    f = new_field()
    for _ in range(20):
        _step(f)
    return render(f), "starfield"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    stars = new_field()
    while stop is None or not stop.is_set():
        if not dry_run:
            try: core.push(device, APP, render(stars))
            except Exception as e: log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  stars={len(stars)}")
        _step(stars)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
