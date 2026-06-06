#!/usr/bin/env python3
"""flipclock — 翻页钟 -> 像素时钟 DIY "flipclock"(插件, 视觉型)

像素翻页钟: HH:MM 大字落在四张深色卡片上, 每张卡片中线有一道翻页缝; 分钟跳变时, 变化的那一位
播放一段向下扫过的翻页动画; 冒号每秒闪一下。整屏一条 db 位图渲染。

单独运行: python3 plugins/flipclock/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "flipclock"
NAME = "翻页钟"
GROUP = "视觉"
DESC = "翻页钟: HH:MM 大字落在深色卡片上, 分钟跳变时翻页动画, 冒号每秒闪。"
DEFAULT_INTERVAL = 1
ITEMS = [APP]
W, H = 52, 16

FONT = {
    "0": ("###", "#.#", "#.#", "#.#", "###"), "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"), "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"), "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"), "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"), "9": ("###", "#.#", "###", "..#", "###"),
    ":": ("...", ".#.", "...", ".#.", "..."),
}
GW, GH = 3, 5
SCALE = 2
DW, DH = GW * SCALE, GH * SCALE                  # 数字 6x10
CW, CH, CY = 9, 14, 1                            # 卡片 宽9 高14 顶y1
CARDS_X = [3, 13, 30, 40]                        # H1 H2 M1 M2 四张卡片左x
COLON_X = 23
DIGIT_Y = 3
SEAM_Y = 8                                       # 卡片中缝所在行
BG = 0x000000
CARD = 0x12222E                                  # 卡片底色(深蓝灰)
SEAM = 0x05080C                                  # 中缝(更暗)
DIGIT = 0xFFFFFF                                 # 数字色
COLON_C = 0x3EE08A                               # 冒号(绿)
SWEEP = 0x9CFFD6                                 # 翻页扫过的高光行


def _fill(px, x, y, w, h, c):
    for Y in range(y, y + h):
        for X in range(x, x + w):
            if 0 <= X < W and 0 <= Y < H:
                px[Y * W + X] = c


def _glyph(px, ch, x0, y0, color):
    g = FONT.get(ch)
    if not g:
        return
    for gy in range(GH):
        for gx in range(GW):
            if g[gy][gx] == "#":
                for sy in range(SCALE):
                    for sx in range(SCALE):
                        X, Y = x0 + gx * SCALE + sx, y0 + gy * SCALE + sy
                        if 0 <= X < W and 0 <= Y < H:
                            px[Y * W + X] = color


def render(hhmm, colon_on, sweep_y=None, sweep_cards=()):
    px = [BG] * (W * H)
    for i, cx in enumerate(CARDS_X):
        _fill(px, cx, CY, CW, CH, CARD)              # 卡片
        for X in range(cx, cx + CW):                 # 中缝
            if 0 <= SEAM_Y < H:
                px[SEAM_Y * W + X] = SEAM
        _glyph(px, hhmm[i], cx + (CW - DW) // 2, DIGIT_Y, DIGIT)
        if sweep_y is not None and i in sweep_cards:  # 翻页高光扫过该卡片
            for X in range(cx, cx + CW):
                if 0 <= sweep_y < H:
                    px[sweep_y * W + X] = SWEEP
    if colon_on:
        _glyph(px, ":", COLON_X, DIGIT_Y, COLON_C)
    return core.bitmap_frame(px)


def frame_for(item, interval):
    return render(time.strftime("%H%M"), True), time.strftime("%H:%M")


def _wait(stop, t):
    """可中断等待; 返回 True 表示应停止。"""
    if stop is not None:
        return stop.wait(t)
    time.sleep(t)
    return False


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    last = "    "
    while stop is None or not stop.is_set():
        now = time.strftime("%H%M")
        colon_on = (int(time.strftime("%S")) % 2 == 0)
        changed = [i for i in range(4) if now[i] != last[i]]
        if not dry_run:
            try:
                if changed and last != "    ":           # 翻页动画: 高光行向下扫过变化的位
                    for sy in (4, 7, 10, 13):
                        core.push(device, APP, render(now, colon_on, sweep_y=sy, sweep_cards=changed))
                        if _wait(stop, 0.06):
                            return
                core.push(device, APP, render(now, colon_on))
            except Exception as e:
                log(f"  push fail: {e}")
        else:
            log(f"{time.strftime('%H:%M:%S')}  flipclock {now[:2]}:{now[2:]}")
        last = now
        if once:
            break
        if _wait(stop, 1.0):
            break


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
