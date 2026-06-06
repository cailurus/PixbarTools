#!/usr/bin/env python3
"""hourly — 整点播报（附属推送插件）

到整点(可选也报半点)时, 在宿主画面上插播当前时间几秒钟, 然后宿主自然恢复。
不依赖外部数据。由控制台的 Attachment 驱动: attach_loop(device, host, options, stop, log, inject)。
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

ATTACH = True
APP = "hourly"
NAME = "整点播报"
DESC = "到整点（可选也报半点）时，在宿主画面上插播当前时间。"
OPTIONS = [
    {"key": "half", "label": "也报半点", "default": "no", "choices": [["no", "否"], ["yes", "是"]]},
    {"key": "hold", "label": "显示(秒)", "type": "number", "default": 6, "min": 2, "max": 60},
    core.color_option("#FFD000"),
]


def _secs_to_next(half):
    """距下一个整点(或半点)的秒数。"""
    lt = time.localtime()
    m, s = lt.tm_min, lt.tm_sec
    if half and m < 30:
        return (30 - m) * 60 - s
    return (60 - m) * 60 - s


def attach_loop(device, host, options, stop, log, inject):
    while not stop.is_set():
        if stop.wait(max(1, _secs_to_next(options.get("half") == "yes"))):
            break
        text = time.strftime("%H:%M")
        hold = int(options.get("hold", 6))
        inject(core.text_frame(text, options.get("color", "#FFD000"), hold), hold)
        log(f"{time.strftime('%H:%M:%S')}  整点: {text}")
