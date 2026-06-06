#!/usr/bin/env python3
"""notice — 通知板 -> 像素时钟 DIY "notice"（插件）

把面板里输入的一句话推到时钟上滚动显示(留言牌)。设备不自动滚动, 故插件做跑马灯。
留言用文本选项即时修改, 颜色可选。注意: 仅 ASCII(重音音译, 中文等被剔除)。

单独运行: python3 plugins/notice/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, time, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "notice"
NAME = "通知板"
GROUP = "工具"
DESC = "通知板：把你在面板输入的一句话推到时钟上滚动显示，当作桌面留言牌。"
DEFAULT_INTERVAL = 1
ITEMS = ["msg"]
OPTIONS = [
    {"key": "msg", "label": "留言", "type": "text", "default": "HELLO PIXBAR"},
    {"key": "color", "label": "颜色", "default": "#00FF66", "choices": [
        ["#FFFFFF", "白"], ["#00FF66", "绿"], ["#FFD000", "黄"], ["#FF3030", "红"],
        ["#4285F4", "蓝"], ["#FF6400", "橙"], ["#00E5FF", "青"], ["#FF6FB5", "粉"]]},
]
SCROLL_TICK = 0.4                    # 每 0.4s 推一帧
STEP = 5
CHAR_W = 6


def ascii_clean(s):
    # 转大写: 设备字体小写有缺字(如小写 t 为空白), 大写字形完整可靠
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return "".join(c for c in s if 0x20 <= ord(c) <= 0x7E).strip()


def build_frame(text, tx, color, centered):
    if centered:                     # 放得下: 居中静态
        t = {"content": text, "fontHeight": 10, "x": -1000, "y": 3,
             "align": "center", "rect": [0, 0, 52, 16], "color": color}
    else:                            # 放不下: 按 tx 滚动
        t = {"content": text, "fontHeight": 10, "x": tx, "y": 3,
             "rect": [0, 0, 52, 16], "color": color}
    return {"duration": 5, "text": [t]}


def frame_for(item, interval):
    """静态快照(供"推一次"): 用默认留言居中。"""
    msg = ascii_clean(OPTIONS[0]["default"]) or "HELLO"
    return build_frame(msg, 0, OPTIONS[1]["default"], True), f"notice: {msg}"


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """跑马灯: 留言宽于屏则每 0.4s 左移滚动, 否则居中静态。留言/颜色改变即时生效。"""
    options = options or {}
    text, x = None, 0
    while stop is None or not stop.is_set():
        msg = ascii_clean(options.get("msg", OPTIONS[0]["default"])) or "HELLO"
        color = options.get("color", OPTIONS[1]["default"])
        if msg != text:                  # 留言变化 -> 重置滚动到右侧入场
            text, x = msg, 52
            log(f"{time.strftime('%H:%M:%S')}  msg: {text}")
        est_w = len(text) * CHAR_W
        centered = est_w <= 52
        if not centered:
            tx = x
            x -= STEP
            if x < -est_w:
                x = 52
        else:
            tx = 0
        if not dry_run:
            try: core.push(device, APP, build_frame(text, tx, color, centered))
            except Exception as e: log(f"  push fail: {e}")
        if once:
            break
        if stop is not None:
            if stop.wait(SCROLL_TICK):
                break
        else:
            time.sleep(SCROLL_TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
