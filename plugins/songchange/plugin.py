#!/usr/bin/env python3
"""songchange — 歌曲切换（附属推送插件, macOS）

轮询 Apple Music / Spotify, 检测到换歌(且在播放)时, 在宿主画面上插播新歌名几秒钟。
与"正在播放"主插件不同: 这个只在切歌瞬间插播, 平时不占画面。
由控制台的 Attachment 驱动: attach_loop(device, host, options, stop, log, inject)。
"""
import os, sys, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

ATTACH = True
APP = "songchange"
NAME = "歌曲切换"
DESC = "检测到 Apple Music / Spotify 换歌时，在宿主画面上插播新歌名。"
OPTIONS = [
    {"key": "hold", "label": "显示(秒)", "type": "number", "default": 6, "min": 2, "max": 60},
    {"key": "poll", "label": "检测间隔(秒)", "type": "number", "default": 3, "min": 1, "max": 30},
    core.color_option("#00E5FF"),
]


def _osa(script):
    try:
        return subprocess.run(["osascript", "-e", script], capture_output=True,
                              text=True, timeout=8).stdout.strip()
    except Exception:
        return ""


def get_now():
    """返回 (title, artist, playing_bool) 或 None。优先 Music, 再 Spotify。"""
    for app in ("Music", "Spotify"):
        if _osa(f'tell application "System Events" to (exists process "{app}")') != "true":
            continue
        state = _osa(f'tell application "{app}" to player state as text')
        if not state:
            continue
        title = _osa(f'tell application "{app}" to name of current track')
        artist = _osa(f'tell application "{app}" to artist of current track')
        if not title and not artist:
            continue
        return title, artist, (state == "playing")
    return None


def display(title, artist):
    t = core.ascii_upper(f"{title} - {artist}")
    return t if any(c.isalnum() for c in t) else "MUSIC"


def attach_loop(device, host, options, stop, log, inject):
    last = None                                # 上一次的 (歌名, 歌手) 原始元组
    while not stop.is_set():
        if stop.wait(max(1, int(options.get("poll", 3)))):
            break
        now = get_now()
        if not now:
            last = None
            continue
        title, artist, playing = now
        key = (title, artist)                  # 按原始曲目判断换歌(避免不同歌都清洗成 MUSIC 而漏判)
        if key != last:
            last = key
            if playing:
                hold = int(options.get("hold", 6))
                inject(core.text_frame(display(title, artist), options.get("color", "#00E5FF"), hold), hold)
                log(f"{time.strftime('%H:%M:%S')}  换歌: {display(title, artist)}")
