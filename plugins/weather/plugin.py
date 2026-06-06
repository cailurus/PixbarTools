#!/usr/bin/env python3
"""weather — 天气氛围场景（主信息流插件）

不是"温度+图标", 而是整屏变成天空: 按真实天气渲染动画场景——
晴(太阳光晕) / 多云(灰云飘) / 雨(雨丝落) / 雪(雪花飘) / 雾(雾带移) / 雷(雨+闪电)。
角落叠加当前温度。数据: open-meteo(免 Key); 城市可在选项里改。

整屏用一条 db 位图渲染(粒子场景), 文字叠当前温度。
单独运行: python3 plugins/weather/plugin.py [--device IP] [--dry-run] [--once]
"""
import os, sys, json, math, random, threading, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "weather"
NAME = "天气氛围"
GROUP = "信息"
DESC = "按真实天气把整屏变成天空：晴/多云/雨/雪/雾/雷的动画场景，叠加当前温度。"
DEFAULT_INTERVAL = 1
ITEMS = ["weather"]
OPTIONS = [{"key": "location", "label": "城市", "type": "search", "endpoint": "/api/geocode",
            "default": "39.9075|116.3972|北京, 北京市, 中国"}]

W, H = 52, 16
TICK = 0.12
FETCH_INTERVAL = 3600               # 每小时重取一次天气
UA = "Mozilla/5.0 pixbar"
_last = None                        # 模块级缓存: (scene, temp, loc); 供"推一次"复用最近一次结果


def _get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=10))


def fetch_weather(location):
    """location 为搜索选中的 "lat|lon|显示名"(无歧义), 或纯城市名(回退地理编码)。
    返回 (scene, temp, 完整位置) 或 None。"""
    global _last
    try:
        if "|" in location:                           # 搜索选中: 直接用经纬度, 不再重新消歧
            lat, lon, loc = location.split("|", 2)
        else:                                          # 纯名字: 地理编码取第一个
            g = _get(f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(location)}&count=1&language=zh")
            r = g["results"][0]
            lat, lon = r["latitude"], r["longitude"]
            loc = ", ".join(x for x in (r.get("name"), r.get("admin1"), r.get("country")) if x)
        lat, lon = float(lat), float(lon)             # 校验为数字, 防把任意串拼进请求 URL
        w = _get(f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code")
        c = w["current"]
        _last = (scene_of(int(c["weather_code"])), int(round(c["temperature_2m"])), loc)
        return _last
    except Exception:
        return None


def scene_of(code):
    if code == 0:
        return "clear"
    if code in (1, 2, 3):
        return "cloud"
    if code in (45, 48):
        return "fog"
    if 71 <= code <= 77 or code in (85, 86):
        return "snow"
    if 95 <= code <= 99:
        return "thunder"
    return "rain"                   # 51-67 / 80-82 等


# ---- 各场景渲染(返回 52*16 行优先像素) ----
def _blank(c=0x000000):
    return [c] * (W * H)


def draw_clear(px, ph):
    cx, cy, r = 40, 5, 4
    glow = 0xFF8A00 if (ph // 6) % 2 else 0xFFB030
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                px[y * W + x] = 0xFFD24B
            elif d <= r + 2.5:
                px[y * W + x] = glow
    # 偶尔的光线
    for a in range(0, 360, 45):
        rr = r + 3 + (ph % 3)
        x = int(cx + rr * math.cos(math.radians(a + ph * 4)))
        y = int(cy + rr * math.sin(math.radians(a + ph * 4)))
        if 0 <= x < W and 0 <= y < H:
            px[y * W + x] = 0xFFC040


# 像素云朵 sprite: * 高光 / # 云体 / % 阴影。配色给出体积感。
_CLOUD_SPRITES = [
    [".....*****....", "...**#####**..", "..*#########*.", ".*###########*", "%############%", ".%%########%%."],
    ["...***....", ".*#####*..", "*#######*.", "%#######%.", ".%%###%%.."],
    ["..**...", ".*##*..", "%####%.", ".%%%%.."],
]
_CLOUD_COL = {"*": 0xAAB0BA, "#": 0x767C86, "%": 0x545A64}


def _init_clouds():
    import random as _r
    cl = []
    for i in range(4):
        si = _r.choice([0, 0, 1, 1, 2])
        cl.append({"x": float(_r.randint(-20, W)), "y": _r.randint(0, 9),
                   "spd": _r.uniform(0.12, 0.26), "si": si})
    return cl


def draw_cloud(px, st):
    import random as _r
    clouds = st.setdefault("clouds", _init_clouds())
    for c in sorted(clouds, key=lambda c: c["spd"]):       # 慢的(远)先画, 快的(近)后画盖上
        sp = _CLOUD_SPRITES[c["si"]]
        cw = len(sp[0])
        c["x"] += c["spd"]
        if c["x"] > W:                                     # 完全飘出右侧 -> 从左侧外重生
            c["x"] = float(-cw - _r.randint(2, 22)); c["y"] = _r.randint(0, 9)
            c["si"] = _r.choice([0, 0, 1, 1, 2])
            sp = _CLOUD_SPRITES[c["si"]]
        bx = int(c["x"])
        for dy, row in enumerate(sp):
            y = c["y"] + dy
            if not (0 <= y < H):
                continue
            for dx, ch in enumerate(row):
                if ch == ".":
                    continue
                x = bx + dx
                if 0 <= x < W:
                    px[y * W + x] = _CLOUD_COL[ch]


def draw_rain(px, st, ph):
    drops = st.setdefault("drops", [[random.randint(0, W - 1), random.uniform(0, H), random.uniform(1.2, 2.2)] for _ in range(34)])
    for d in drops:
        d[1] += d[2]
        if d[1] >= H:
            d[0] = random.randint(0, W - 1); d[1] = -1
        x, y = int(d[0]), int(d[1])
        if 0 <= y < H:
            px[y * W + x] = 0x3A78FF
            if y - 1 >= 0:
                px[(y - 1) * W + x] = 0x1E4AA0


def draw_snow(px, st, ph):
    flakes = st.setdefault("flakes", [[random.uniform(0, W), random.uniform(0, H), random.uniform(0.3, 0.7)] for _ in range(26)])
    for f in flakes:
        f[1] += f[2]
        f[0] += math.sin((f[1] + ph) * 0.3) * 0.3
        if f[1] >= H:
            f[0] = random.uniform(0, W); f[1] = -1
        x, y = int(f[0]) % W, int(f[1])
        if 0 <= y < H:
            px[y * W + x] = 0xFFFFFF


def draw_fog(px, ph):
    for y in range(H):
        base = 0x20262E + (y % 3) * 0x060606
        for x in range(W):
            v = (math.sin((x + ph) * 0.2 + y) + 1) / 2
            g = int(40 + 70 * v)
            px[y * W + x] = (g << 16) | (g << 8) | (g + 10)


def draw_thunder(px, st, ph):
    draw_rain(px, st, ph)
    if st.get("flash", 0) > 0:
        st["flash"] -= 1
        for i in range(W * H):
            px[i] = 0xFFFFFF
    elif random.random() < 0.03:
        st["flash"] = 1


def render(scene, temp, st, ph, interval):
    px = _blank()
    if scene == "clear":
        draw_clear(px, ph)
    elif scene == "cloud":
        draw_cloud(px, st)
    elif scene == "snow":
        draw_snow(px, st, ph)
    elif scene == "fog":
        draw_fog(px, ph)
    elif scene == "thunder":
        draw_thunder(px, st, ph)
    else:
        draw_rain(px, st, ph)
    frame = core.bitmap_frame(px, duration=interval)
    if temp is not None:                 # 角落叠温度
        frame["text"] = [{"content": f"{temp}C", "fontHeight": 10, "x": 1, "y": 3, "color": "#FFFFFF"}]
    return frame


def frame_for(item, interval):
    """推一次: 用最近一次缓存(若有), 否则拉默认城市。"""
    r = _last or fetch_weather(OPTIONS[0]["default"])
    scene, temp = (r[0], r[1]) if r else ("cloud", None)
    return render(scene, temp, {}, 0, interval), (f"{r[2]}: {scene} {temp}C" if r else "weather n/a")


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """每小时取一次天气(改城市立即重取); 每 TICK 推一帧动画。天气结果写进日志。"""
    options = options or {}
    box = {"scene": "cloud", "temp": None}
    lock = threading.Lock()

    def fetch(city):
        r = fetch_weather(city)
        if r:
            with lock:
                box["scene"], box["temp"] = r[0], r[1]
            log(f"{time.strftime('%H:%M:%S')}  {r[2]} · {r[0]} · {r[1]}C")
        else:
            log(f"{time.strftime('%H:%M:%S')}  取天气失败: {city}")

    DEFAULT = OPTIONS[0]["default"]
    cur_city = options.get("location", DEFAULT)
    fetch(cur_city)
    last_fetch = time.monotonic()
    st = {}
    while stop is None or not stop.is_set():
        city = options.get("location", DEFAULT)
        now = time.monotonic()
        if city != cur_city or now - last_fetch >= FETCH_INTERVAL:   # 改城市立即重取, 否则每小时
            cur_city = city; last_fetch = now
            threading.Thread(target=fetch, args=(city,), daemon=True).start()
        with lock:
            scene, temp = box["scene"], box["temp"]
        frame = render(scene, temp, st, int(now / TICK), interval)
        if not dry_run:
            try: core.push(device, APP, frame)
            except Exception as e: log(f"  push fail: {e}")
        if once:
            break
        if stop is not None:
            if stop.wait(TICK):
                break
        else:
            time.sleep(TICK)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
