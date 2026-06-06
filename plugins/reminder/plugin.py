#!/usr/bin/env python3
"""reminder — 定时提醒（附属推送插件）

附属推送类型: 不占自己的设备组件, 必须挂在某个主信息流插件上。
每隔 N 分钟, 在宿主画面上插播一句提醒文字(如站起来喝水)几秒钟, 然后宿主自然恢复。
由控制台的 Attachment 驱动: attach_loop(device, host, options, stop, log, inject)。
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

ATTACH = True                       # 标记为附属推送类型(不在左侧列表单独出现)
APP = "reminder"
NAME = "定时提醒"
DESC = "每隔一段时间，在宿主画面上插播一句提醒（如站起来喝水）。"
OPTIONS = [
    {"key": "text", "label": "文字", "type": "text", "default": "DRINK WATER"},
    {"key": "every", "label": "间隔(分钟)", "type": "number", "default": 45, "min": 1, "max": 600},
    {"key": "hold", "label": "显示(秒)", "type": "number", "default": 8, "min": 2, "max": 60},
    core.color_option("#3EE08A"),
]


def attach_loop(device, host, options, stop, log, inject):
    """每 every 分钟插播一次。stop/inject 由控制台(Attachment)保证传入。"""
    while not stop.is_set():
        if stop.wait(max(1, int(options.get("every", 45))) * 60):
            break
        text = core.ascii_upper(options.get("text", "DRINK WATER")) or "REMINDER"
        hold = int(options.get("hold", 8))
        inject(core.text_frame(text, options.get("color", "#3EE08A"), hold), hold)
        log(f"{time.strftime('%H:%M:%S')}  插播: {text}")
