#!/usr/bin/env python3
"""timer — 竖装距离计时柱 -> 像素时钟 DIY "timer"(插件, 工具)

为"架在三脚架上、竖过来、离得远"设计的间歇/训练计时器: 一根随时间下沉的彩色光柱 +
大号秒数,隔着房间靠"柱子还剩多高"就能一眼读到还剩多少。练=绿 / 歇=黄 / 最后 3 秒=红。
设 练X秒 / 歇Y秒 / 几组, 开启即从头跑; 跑完显示完成态直到关闭。

竖装渲染: 先在"竖立坐标系"(16 宽 × 52 高)里正常画好, 再整体旋转 90° 落进设备的 52×16。
朝向可选: 竖装 / 竖装(翻转, 接口朝另一边) / 横装(放桌面)。

单独运行: python3 plugins/timer/plugin.py [--device IP] [--dry-run] [--once]
"""
import math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "timer"
NAME = "计时柱"
GROUP = "工具"
DESC = "竖装训练计时器: 下沉光柱 + 大秒数, 设 练/歇/组数, 远处一眼读剩余。练绿/歇黄/末3秒红。"
DEFAULT_INTERVAL = 1
ITEMS = [APP]
OPTIONS = [
    {"key": "work", "label": "练(秒)", "type": "number", "default": 30, "min": 1, "max": 3600},
    {"key": "rest", "label": "歇(秒)", "type": "number", "default": 15, "min": 0, "max": 3600},
    {"key": "rounds", "label": "组数", "type": "number", "default": 8, "min": 1, "max": 99},
    {"key": "orient", "label": "朝向", "default": "pv",
     "choices": [["pv", "竖装"], ["pv2", "竖装(翻转)"], ["land", "横装"]]},
]

W, H = 52, 16          # 设备缓冲(横)
PW, PH = 16, 52        # 竖立逻辑画布(在这里正常画, 再旋转)
BG = 0x000000
WORK = 0x00FF66
REST = 0xFFD000
RED = 0xFF3030
WHITE = 0xFFFFFF
DOT = 0x4A5560        # 组数小点(暗)
TICK = 0.4

FONT = {
    "0": ("###", "#.#", "#.#", "#.#", "###"), "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"), "3": ("###", "..#", "###", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"), "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"), "7": ("###", "..#", ".#.", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"), "9": ("###", "#.#", "###", "..#", "###"),
}
GW, GH = 3, 5


def _dim(c, f):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return (int(r * f) << 16) | (int(g * f) << 8) | int(b * f)


def _text_w(s, scale):
    return len(s) * GW * scale + (len(s) - 1) * scale


def _draw_text(buf, bw, bh, s, x0, y0, scale, color):
    cx = x0
    for ch in s:
        g = FONT.get(ch)
        if g:
            for gy in range(GH):
                for gx in range(GW):
                    if g[gy][gx] == "#":
                        for sy in range(scale):
                            for sx in range(scale):
                                x, y = cx + gx * scale + sx, y0 + gy * scale + sy
                                if 0 <= x < bw and 0 <= y < bh:
                                    buf[y * bw + x] = color
        cx += (GW + 1) * scale


def render_portrait(kind, secs, frac, rounds_left, flip):
    """在 16x52 竖画布上: 底部上沉的光柱 + 居中大秒数 + 顶部组数点; 再旋转进 52x16。"""
    pp = [BG] * (PW * PH)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    # 光柱: 底部锚定, 高度 = frac*PH, 随时间下沉
    filled = int(round(max(0.0, min(1.0, frac)) * PH))
    col = _dim(base, 0.65)
    for py in range(PH - filled, PH):
        for px in range(PW):
            if 0 <= py < PH:
                pp[py * PW + px] = col
    # 组数小点(顶部一排)
    n = min(rounds_left, 7)
    if n > 0:
        tot = n * 2 + (n - 1)
        sx = (PW - tot) // 2
        for i in range(n):
            x = sx + i * 3
            for dx in range(2):
                if 0 <= x + dx < PW:
                    pp[2 * PW + x + dx] = DOT
                    pp[3 * PW + x + dx] = DOT
    # 大秒数(居中, 白)
    s = str(secs)
    scale = 3 if len(s) == 1 else 2 if len(s) == 2 else 1
    tw = _text_w(s, scale)
    _draw_text(pp, PW, PH, s, (PW - tw) // 2, (PH - GH * scale) // 2, scale, WHITE)
    # 旋转 90° 落进设备缓冲
    dev = [BG] * (W * H)
    for py in range(PH):
        for px in range(PW):
            c = pp[py * PW + px]
            if c == BG:
                continue
            bx, by = (W - 1 - py, px) if flip else (py, PW - 1 - px)
            dev[by * W + bx] = c
    return core.bitmap_frame(dev)


def render_landscape(kind, secs, frac, rounds_left):
    """横放(桌面): 大秒数在左 + 底部横向下沉条 + 右上组数点。"""
    px = [BG] * (W * H)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    # 底部横条: 宽 = frac*W, 从满宽缩短
    barw = int(round(max(0.0, min(1.0, frac)) * W))
    col = _dim(base, 0.7)
    for y in range(13, 16):
        for x in range(barw):
            px[y * W + x] = col
    # 大秒数(左, 白, 高 10)
    s = str(secs)
    scale = 2 if len(s) <= 2 else 1
    _draw_text(px, W, H, s, 2, 1, scale, WHITE)
    # 组数点(右上)
    n = min(rounds_left, 6)
    for i in range(n):
        x = W - 2 - i * 3
        if 0 <= x - 1 < W:
            px[1 * W + x - 1] = DOT
            px[1 * W + x] = DOT
    return core.bitmap_frame(px)


def _render(kind, secs, frac, rounds_left, orient):
    if orient == "land":
        return render_landscape(kind, secs, frac, rounds_left)
    return render_portrait(kind, secs, frac, rounds_left, flip=(orient == "pv2"))


def _done_frame(orient):
    return _render("work", 0, 1.0, 0, orient)


def _clampint(v, default, lo, hi):
    try:
        return max(lo, min(hi, int(float(v))))
    except Exception:
        return default


def build_phases(work, rest, rounds):
    """[(kind, 秒, 剩余组数), ...]; 末组后不再歇。"""
    ph = []
    for r in range(rounds):
        ph.append(("work", work, rounds - r))
        if rest > 0 and r < rounds - 1:
            ph.append(("rest", rest, rounds - r - 1))
    return ph


def frame_for(item, interval):
    """push_once / standalone --once: 给一帧满柱预览(练 + 设定秒数)。"""
    return render_portrait("work", 30, 1.0, 8, flip=False), "timer preview"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    opt = options or {}
    work = _clampint(opt.get("work"), 30, 1, 3600)
    rest = _clampint(opt.get("rest"), 15, 0, 3600)
    rounds = _clampint(opt.get("rounds"), 8, 1, 99)
    orient = opt.get("orient", "pv")
    phases = build_phases(work, rest, rounds)

    def emit(frame, line):
        ts = time.strftime("%H:%M:%S")
        if dry_run:
            log(f"{ts}  {line}")
        else:
            try:
                core.push(device, APP, frame)
            except Exception as e:
                log(f"  push fail: {e}")

    if once:
        kind, dur, rl = phases[0]
        emit(_render(kind, dur, 1.0, rl, orient), f"{kind} {dur}s r{rl}")
        return

    for kind, dur, rl in phases:
        end = time.monotonic() + dur
        while stop is None or not stop.is_set():
            rem = end - time.monotonic()
            if rem <= 0:
                break
            secs = int(math.ceil(rem))
            emit(_render(kind, secs, rem / dur, rl, orient), f"{kind} {secs:3d}s r{rl}")
            wait = min(TICK, max(0.05, rem))
            if stop is not None and stop.wait(wait):
                return
            elif stop is None:
                time.sleep(wait)
        if stop is not None and stop.is_set():
            return
    # 完成: 保持完成态直到关闭
    while stop is None or not stop.is_set():
        emit(_done_frame(orient), "done")
        if stop is None or stop.wait(1.0):
            break


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
