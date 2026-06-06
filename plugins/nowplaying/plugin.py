#!/usr/bin/env python3
"""nowplaying — 正在播放 -> 像素时钟 DIY "nowplaying"（插件, macOS）

抓 Apple Music / Spotify 当前曲目, 显示 左侧播放/暂停图标 + 右侧"歌名 - 歌手"。
设备不自动滚动长文本, 故由插件做跑马灯: 文字过宽时每个 tick 横向移位、循环滚动。
注意: 设备只支持 ASCII(0x20–0x7E): 重音字符做音译(café->cafe), 中文等无法显示的字符被剔除;
   清洗后为空时回退显示 "MUSIC"。

数据源: osascript(AppleScript) 查 Music/Spotify。
滚动节奏与面板 interval 解耦: 主循环固定每 SCROLL_TICK(0.5s)匀速推一帧;
播放器查询(osascript 较重, 会阻塞)放在后台线程每 QUERY_INTERVAL(2s)异步刷新, 不卡滚动。
单独运行: python3 plugins/nowplaying/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, subprocess, threading, time, unicodedata
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "nowplaying"
NAME = "正在播放"
GROUP = "信息"
DESC = "正在播放：显示 Apple Music / Spotify 的当前曲目，名字过长时跑马灯滚动。"
DEFAULT_INTERVAL = 1                 # 面板显示用; 实际滚动节奏由 SCROLL_TICK 决定
ITEMS = ["now"]
RECT_X, RECT_W = 9, 43               # 文字区: x=9 起, 宽 43(图标占左侧 0..8)
STEP = 5                             # 每 tick 滚动像素
CHAR_W = 6                           # 10px 字符约宽(估算, 用于判断是否需滚动/何时回卷)
SCROLL_TICK = 0.5                    # 每 0.5s 匀速推一帧(滚动节奏)
QUERY_INTERVAL = 2.0                 # 后台线程每 2s 查一次播放器
DURATION = 5                         # 帧 duration(设备 DIY 轮播停留秒数)


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


def ascii_clean(s):
    """重音音译 + 仅保留可见 ASCII(0x20–0x7E)。"""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c for c in s if 0x20 <= ord(c) <= 0x7E).strip()


def display_text(title, artist):
    """歌名 - 歌手, ASCII 清洗 + 转大写(设备字体小写有缺字); 无字母数字(如全中文)则回退 MUSIC。"""
    t = ascii_clean(f"{title} - {artist}")
    return t.upper() if any(c.isalnum() for c in t) else "MUSIC"


def _icon(playing):
    """左侧播放(绿三角)/暂停(灰双竖)图标 draw 指令。"""
    if playing:
        return [{"df": [2, 5, 1, 6, "#00FF66"]}, {"df": [3, 6, 1, 4, "#00FF66"]},
                {"df": [4, 7, 1, 2, "#00FF66"]}]
    return [{"df": [2, 5, 2, 6, "#888888"]}, {"df": [6, 5, 2, 6, "#888888"]}]


def build_frame(text, tx, playing):
    return {
        "duration": DURATION,
        "text": [{"content": text or " ", "fontHeight": 10, "x": tx, "y": 3,
                  "color": "#FFFFFF", "rect": [RECT_X, 0, RECT_W, 16]}],
        "draw": _icon(playing),
    }


def frame_for(item, interval):
    """静态快照(供"推一次"): 显示当前曲目左对齐, 不滚动。"""
    now = get_now()
    if not now:
        return build_frame("NO MUSIC", 0, False), "no music"
    title, artist, playing = now
    text = display_text(title, artist)
    return build_frame(text, 0, playing), f"{'>' if playing else '||'} {text}"


def _query():
    """同步查一次播放器 -> (text, playing) 或 None。"""
    now = get_now()
    return None if not now else (display_text(now[0], now[1]), now[2])


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """跑马灯: 主循环每 SCROLL_TICK 匀速推一帧; 播放器查询放后台线程, 绝不阻塞滚动。
    曲目变化重置滚动到右侧入场。面板 interval 不影响滚动节奏。"""
    if once:                                        # 单次: 同步查一次推一帧即可
        c = _query()
        frame = build_frame("NO MUSIC", 0, False) if c is None else build_frame(c[0], 0, c[1])
        if not dry_run:
            try: core.push(device, APP, frame)
            except Exception as e: log(f"  push fail: {e}")
        log(f"{time.strftime('%H:%M:%S')}  {'no music' if c is None else c[0]}")
        return

    box = {"c": _query()}                            # 共享曲目信息(后台线程写, 主循环读)
    lock = threading.Lock()
    pstop = stop if stop is not None else threading.Event()

    def poller():                                   # 后台: 每 2s 异步刷新, 不卡主循环
        while not pstop.is_set():
            if pstop.wait(QUERY_INTERVAL):
                break
            c = _query()
            with lock:
                box["c"] = c
    threading.Thread(target=poller, daemon=True).start()

    text, x = None, 0
    while not pstop.is_set():
        with lock:
            cached = box["c"]
        ts = time.strftime("%H:%M:%S")
        if cached is None:
            if text is not None:
                log(f"{ts}  no music")              # 仅在状态切换时记一行
            text = None
            frame = build_frame("NO MUSIC", 0, False)
        else:
            disp, playing = cached
            if disp != text:                        # 换歌 -> 重置滚动 + 记一行
                text, x = disp, RECT_W
                log(f"{ts}  {'>' if playing else '||'} {text}")
            est_w = len(text) * CHAR_W
            if est_w <= RECT_W:                      # 放得下 -> 静态左对齐
                tx = 0
            else:                                    # 放不下 -> 滚动
                tx = x
                x -= STEP
                if x < -est_w:
                    x = RECT_W                       # 滚完从右侧回卷
            frame = build_frame(text, tx, playing)
        if not dry_run:
            try: core.push(device, APP, frame)
            except Exception as e: log(f"  push fail: {e}")
        if pstop.wait(SCROLL_TICK):
            break


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
