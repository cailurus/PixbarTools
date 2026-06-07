#!/usr/bin/env python3
"""timer — 竖装距离计时柱 -> 像素时钟 DIY "timer"(插件, 工具)

为"架在三脚架上、竖过来、离得远"设计的间歇/训练计时器: 一根随时间下沉的彩色光柱 +
大号秒数。练=绿 / 歇=黄 / 最后 3 秒=红。设 练X秒 / 歇Y秒 / 几组, 开启即从头跑; 跑完显示完成态。

竖装渲染: 先在"竖立坐标系"(16 宽 × 52 高)里正常画好, 再整体旋转 90° 落进设备 52×16。
数字用纯方块像素字体(横平竖直, 无斜折)。
朝向: 竖装 / 竖装(翻转) / 横装(放桌面)。数字: 竖排(两位上下堆叠, 大) / 横排(并排) / 不显示(只要光柱)。

单独运行: python3 plugins/timer/plugin.py [--device IP] [--dry-run] [--once]
"""
import math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "timer"
NAME = "计时柱"
GROUP = "工具"
DESC = "竖装训练计时器: 下沉光柱 + 大方块秒数, 设 练/歇/组数; 数字可竖排/横排/不显示, 远处一眼读剩余。"
DEFAULT_INTERVAL = 1
ITEMS = [APP]
OPTIONS = [
    {"key": "work", "label": "练(秒)", "type": "number", "default": 30, "min": 1, "max": 3600},
    {"key": "rest", "label": "歇(秒)", "type": "number", "default": 15, "min": 0, "max": 3600},
    {"key": "rounds", "label": "组数", "type": "number", "default": 8, "min": 1, "max": 99},
    {"key": "orient", "label": "朝向", "default": "pv",
     "choices": [["pv", "竖装"], ["pv2", "竖装(翻转)"], ["land", "横装"]]},
    {"key": "digits", "label": "数字", "default": "v",
     "choices": [["v", "竖排(大)"], ["h", "横排"], ["none", "不显示"]]},
]

W, H = 52, 16          # 设备缓冲(横)
PW, PH = 16, 52        # 竖立逻辑画布
BG = 0x000000
WORK = 0x00FF66
REST = 0xFFD000
RED = 0xFF3030
WHITE = 0xFFFFFF
DOT = 0x4A5560
TICK = 0.2

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


def _fit_scale(buf_w, s):
    """选能在宽 buf_w 内并排放下整串数字的最大 scale。"""
    for sc in (3, 2, 1):
        if len(s) * GBW * sc + (len(s) - 1) * sc <= buf_w:
            return sc
    return 1


def _draw_horizontal(buf, bw, bh, s, color):
    scale = _fit_scale(bw, s)
    tw = len(s) * GBW * scale + (len(s) - 1) * scale
    cx = (bw - tw) // 2
    y0 = (bh - GBH * scale) // 2
    for ch in s:
        _blit(buf, bw, bh, ch, cx, y0, scale, color)
        cx += (GBW + 1) * scale


def _draw_stacked(buf, bw, bh, s, color):
    """两位上下堆叠(放大); 单位数一个超大字。"""
    if len(s) == 1:
        scale = 3
        _blit(buf, bw, bh, s, (bw - GBW * scale) // 2, (bh - GBH * scale) // 2, scale, color)
        return
    scale = 2
    gap = 4
    th = GBH * scale
    x0 = (bw - GBW * scale) // 2
    y0 = (bh - (th * 2 + gap)) // 2
    _blit(buf, bw, bh, s[0], x0, y0, scale, color)
    _blit(buf, bw, bh, s[1], x0, y0 + th + gap, scale, color)


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


def render_portrait(kind, secs, frac, rounds_left, flip, digmode):
    """16x52 竖画布: 底部上沉光柱 + 数字(竖排/横排/不显示) + 顶部组数点, 再旋转进 52x16。"""
    pp = [BG] * (PW * PH)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    exact = max(0.0, min(1.0, frac)) * PH            # 亚像素: 顶端按小数渐暗 -> 连续下沉, 不卡台阶
    full = int(exact)
    colf = _dim(base, 0.6)
    for py in range(PH - full, PH):
        for px in range(PW):
            pp[py * PW + px] = colf
    ftop = exact - full
    if full < PH and ftop > 0.04:
        tcol = _dim(colf, ftop)
        ty = PH - full - 1
        for px in range(PW):
            pp[ty * PW + px] = tcol
    _row_dots(pp, PW, 0, rounds_left, DOT)
    s = str(secs)
    if digmode == "none":
        pass
    elif digmode == "h":
        _draw_horizontal(pp, PW, PH, s, WHITE)
    elif len(s) <= 2:                                 # v: 竖排堆叠(三位以上自动并排)
        _draw_stacked(pp, PW, PH, s, WHITE)
    else:
        _draw_horizontal(pp, PW, PH, s, WHITE)
    dev = [BG] * (W * H)
    for py in range(PH):
        for px in range(PW):
            c = pp[py * PW + px]
            if c == BG:
                continue
            bx, by = (W - 1 - py, px) if flip else (py, PW - 1 - px)
            dev[by * W + bx] = c
    return core.bitmap_frame(dev)


def render_landscape(kind, secs, frac, rounds_left, digmode):
    """横放(桌面): 方块数字在左 + 底部横向下沉条 + 右上组数点。"""
    px = [BG] * (W * H)
    base = RED if secs <= 3 else (WORK if kind == "work" else REST)
    exact = max(0.0, min(1.0, frac)) * W             # 亚像素: 右端按小数渐暗 -> 平滑收缩
    full = int(exact)
    colf = _dim(base, 0.7)
    for y in range(14, 16):
        for x in range(full):
            px[y * W + x] = colf
    ftop = exact - full
    if full < W and ftop > 0.04:
        tcol = _dim(colf, ftop)
        for y in range(14, 16):
            px[y * W + full] = tcol
    if digmode != "none":
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


def _render(kind, secs, frac, rounds_left, orient, digmode):
    if orient == "land":
        return render_landscape(kind, secs, frac, rounds_left, digmode)
    return render_portrait(kind, secs, frac, rounds_left, flip=(orient == "pv2"), digmode=digmode)


def _done_frame(orient, digmode):
    return _render("work", 0, 1.0, 0, orient, digmode)


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
    return render_portrait("work", 26, 1.0, 8, flip=False, digmode="v"), "timer preview"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    opt = options or {}
    # 数值类(练/歇/组数)开机时快照 — 跑到一半改不打乱当前计时, 下次开启生效
    work = _clampint(opt.get("work"), 30, 1, 3600)
    rest = _clampint(opt.get("rest"), 15, 0, 3600)
    rounds = _clampint(opt.get("rounds"), 8, 1, 99)
    phases = build_phases(work, rest, rounds)

    def disp():                                   # 显示类(朝向/数字)每帧实时读, 调整即时反映到设备
        return opt.get("orient", "pv"), opt.get("digits", "v")

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
        o, d = disp()
        emit(_render(kind, dur, 1.0, rl, o, d), f"{kind} {dur}s r{rl}")
        return

    for kind, dur, rl in phases:
        end = time.monotonic() + dur
        while stop is None or not stop.is_set():
            rem = end - time.monotonic()
            if rem <= 0:
                break
            secs = int(math.ceil(rem))
            o, d = disp()
            emit(_render(kind, secs, rem / dur, rl, o, d), f"{kind} {secs:3d}s r{rl}")
            wait = min(TICK, max(0.05, rem))
            if stop is not None and stop.wait(wait):
                return
            elif stop is None:
                time.sleep(wait)
        if stop is not None and stop.is_set():
            return
    while stop is None or not stop.is_set():
        o, d = disp()
        emit(_done_frame(o, d), "done")
        if stop is None or stop.wait(1.0):
            break


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
