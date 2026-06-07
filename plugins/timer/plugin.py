#!/usr/bin/env python3
"""timer — 竖装距离计时柱 -> 像素时钟 DIY "timer"(插件, 工具)

为"架在三脚架上、竖过来、离得远"设计的间歇/训练计时器: 一根随时间下沉的彩色光柱 +
大号秒数。竖装时两位数字上下堆叠(26 = 上 2 下 6), 字号更大、远处更易读。
练=绿 / 歇=黄 / 最后 3 秒=红。设 练X秒 / 歇Y秒 / 几组, 开启即从头跑; 跑完显示完成态。

竖装渲染: 先在"竖立坐标系"(16 宽 × 52 高)里正常画好, 再整体旋转 90° 落进设备 52×16。
数字用纯方块像素字体(横平竖直, 无斜折)。朝向: 竖装 / 竖装(翻转) / 横装(放桌面)。

单独运行: python3 plugins/timer/plugin.py [--device IP] [--dry-run] [--once]
"""
import math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "timer"
NAME = "计时柱"
GROUP = "工具"
DESC = "竖装训练计时器: 下沉光柱 + 大方块秒数(竖装上下堆叠), 设 练/歇/组数, 远处一眼读剩余。"
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
PW, PH = 16, 52        # 竖立逻辑画布
BG = 0x000000
WORK = 0x00FF66
REST = 0xFFD000
RED = 0xFF3030
WHITE = 0xFFFFFF
DOT = 0x4A5560
TICK = 0.4

# 纯方块像素数字 5x9: 横平竖直, 无斜折(7 = 一横 + 一竖)
BIG = {
    "0": ("#####", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#...#", "#####"),
    "1": ("..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "2": ("#####", "....#", "....#", "....#", "#####", "#....", "#....", "#....", "#####"),
    "3": ("#####", "....#", "....#", "....#", "#####", "....#", "....#", "....#", "#####"),
    "4": ("#...#", "#...#", "#...#", "#...#", "#####", "....#", "....#", "....#", "....#"),
    "5": ("#####", "#....", "#....", "#....", "#####", "....#", "....#", "....#", "#####"),
    "6": ("#####", "#....", "#....", "#....", "#####", "#...#", "#...#", "#...#", "#####"),
    "7": ("#####", "....#", "....#", "....#", "....#", "....#", "....#", "....#", "....#"),
    "8": ("#####", "#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#", "#####"),
    "9": ("#####", "#...#", "#...#", "#...#", "#####", "....#", "....#", "....#", "#####"),
}
GBW, GBH = 5, 9


def _dim(c, f):
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    return (int(r * f) << 16) | (int(g * f) << 8) | int(b * f)


def _blit(buf, bw, bh, ch, x0, y0, scale, color):
    g = BIG.get(ch)
    if not g:
        return
    for gy in range(GBH):
        for gx in range(GBW):
            if g[gy][gx] == "#":
                for sy in range(scale):
                    for sx in range(scale):
                        x, y = x0 + gx * scale + sx, y0 + gy * scale + sy
                        if 0 <= x < bw and 0 <= y < bh:
                            buf[y * bw + x] = color


def _row_dots(buf, bw, py, n, color):
    n = min(n, 8)
    if n <= 0:
        return
    tot = n * 2 - 1
    sx = (bw - tot) // 2
    for i in range(n):
        x = sx + i * 2
        if 0 <= x < bw:
            buf[py * bw + x] = color


def render_portrait(kind, secs, frac, rounds_left, flip):
    """16x52 竖画布: 底部上沉光柱 + 居中大数字(两位上下堆叠) + 顶部组数点, 再旋转进 52x16。"""
    pp = [BG] * (PW * PH)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    filled = int(round(max(0.0, min(1.0, frac)) * PH))
    col = _dim(base, 0.6)
    for py in range(PH - filled, PH):
        for px in range(PW):
            if 0 <= py < PH:
                pp[py * PW + px] = col
    _row_dots(pp, PW, 0, rounds_left, DOT)
    s = str(secs)
    if len(s) == 1:                                   # 单位数: 一个超大字居中
        scale = 3
        _blit(pp, PW, PH, s, (PW - GBW * scale) // 2, (PH - GBH * scale) // 2, scale, WHITE)
    elif len(s) == 2:                                 # 两位数: 上下堆叠, 各放大
        scale = 2
        gap = 4
        th = GBH * scale
        x0 = (PW - GBW * scale) // 2
        y0 = (PH - (th * 2 + gap)) // 2
        _blit(pp, PW, PH, s[0], x0, y0, scale, WHITE)
        _blit(pp, PW, PH, s[1], x0, y0 + th + gap, scale, WHITE)
    else:                                             # 3 位(>=100s, 少见): 并排小号
        scale = 1
        tw = len(s) * GBW * scale + (len(s) - 1) * scale
        cx = (PW - tw) // 2
        for ch in s:
            _blit(pp, PW, PH, ch, cx, (PH - GBH * scale) // 2, scale, WHITE)
            cx += (GBW + 1) * scale
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
    """横放(桌面): 方块数字在左 + 底部横向下沉条 + 右上组数点。"""
    px = [BG] * (W * H)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    barw = int(round(max(0.0, min(1.0, frac)) * W))
    col = _dim(base, 0.7)
    for y in range(14, 16):
        for x in range(barw):
            px[y * W + x] = col
    s = str(secs)
    cx = 2
    for ch in s:
        _blit(px, W, H, ch, cx, 2, 1, WHITE)
        cx += (GBW + 1)
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
    """push_once / standalone --once: 满柱预览(练 + 26 秒, 竖排)。"""
    return render_portrait("work", 26, 1.0, 8, flip=False), "timer preview"


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
    while stop is None or not stop.is_set():
        emit(_done_frame(orient), "done")
        if stop is None or stop.wait(1.0):
            break


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
