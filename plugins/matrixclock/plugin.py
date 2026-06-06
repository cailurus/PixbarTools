#!/usr/bin/env python3
"""matrixclock — Matrix 数字雨时钟 -> 像素时钟 DIY "matrixclock"(插件, 视觉型)

绿色代码雨从顶部不断落下(头部近白、拖尾渐暗的绿), 中央叠加当前时间 HH:MM(白字, 背后压暗以突出)。
整屏一条 db 位图渲染, 自带 run_loop 控制帧率。

单独运行: python3 plugins/matrixclock/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, random, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "matrixclock"
NAME = "数字雨时钟"
GROUP = "视觉"
DESC = "Matrix 数字雨: 绿色代码雨不断下落, 中央叠加当前时间 HH:MM。"
DEFAULT_INTERVAL = 1
ITEMS = [APP]
W, H = 52, 16
TICK = 0.1
BG = 0x000000

# 内嵌 3x5 数字字体(含冒号); 时间放大 2x 叠在雨上
FONT = {
    "0": ("###", "#.#", "#.#", "#.#", "###"), "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"), "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"), "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"), "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"), "9": ("###", "#.#", "###", "..#", "###"),
    ":": ("...", ".#.", "...", ".#.", "..."),
}
GW, GH = 3, 5


def _green(v):
    """v:0..255 -> 偏纯绿(红蓝压暗)。"""
    v = max(0, min(255, int(v)))
    return ((v // 5) << 16) | (v << 8) | (v // 5)


def _new_drop():
    return {"y": random.uniform(-H, 0), "spd": random.uniform(0.4, 1.1), "len": random.randint(4, 11)}


def new_rain():
    return [(_new_drop() if random.random() < 0.5 else None) for _ in range(W)]


def _step(cols):
    for x in range(W):
        d = cols[x]
        if d is None:
            if random.random() < 0.03:               # 偶尔点亮一列
                cols[x] = _new_drop()
            continue
        d["y"] += d["spd"]
        if d["y"] - d["len"] > H:                     # 整条落出屏 -> 重生 / 熄灭
            cols[x] = _new_drop() if random.random() < 0.7 else None


def _overlay_time(px):
    s = time.strftime("%H:%M")
    scale, gap = 2, 1
    tw = (len(s) * GW + (len(s) - 1) * gap) * scale
    th = GH * scale
    x0 = (W - tw) // 2
    y0 = (H - th) // 2
    for Y in range(y0 - 1, y0 + th + 1):             # 时间区域压暗, 让白字突出
        for X in range(x0 - 1, x0 + tw + 1):
            if 0 <= X < W and 0 <= Y < H:
                c = px[Y * W + X]
                px[Y * W + X] = (((c >> 16 & 255) // 6) << 16) | (((c >> 8 & 255) // 6) << 8) | ((c & 255) // 6)
    cx = x0                                           # 画白色时间
    for ch in s:
        g = FONT.get(ch)
        if g:
            for gy in range(GH):
                for gx in range(GW):
                    if g[gy][gx] == "#":
                        for sy in range(scale):
                            for sx in range(scale):
                                X, Y = cx + gx * scale + sx, y0 + gy * scale + sy
                                if 0 <= X < W and 0 <= Y < H:
                                    px[Y * W + X] = 0xFFFFFF
        cx += (GW + gap) * scale


def render(cols):
    px = [BG] * (W * H)
    for x in range(W):
        d = cols[x]
        if d is None:
            continue
        for k in range(d["len"]):
            yy = int(d["y"]) - k
            if 0 <= yy < H:
                px[yy * W + x] = 0xCCFFCC if k == 0 else _green(230 - k * (200 / max(1, d["len"])))
    _overlay_time(px)
    return core.bitmap_frame(px)


def frame_for(item, interval):
    cols = new_rain()
    for _ in range(12):
        _step(cols)
    return render(cols), time.strftime("%H:%M")


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    cols = new_rain()
    while stop is None or not stop.is_set():
        if not dry_run:
            try:
                core.push(device, APP, render(cols))
            except Exception as e:
                log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  matrixclock {time.strftime('%H:%M')}")
        _step(cols)
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
