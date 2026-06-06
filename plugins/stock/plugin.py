#!/usr/bin/env python3
"""stock — 美股价格 -> 像素时钟 DIY "stock"（插件）

AAPL/MSFT/NVDA/GOOGL 轮播: 左侧公司 logo + 右侧实时价 + 涨绿跌红。
数据: Yahoo Finance 公开接口(无需 Key)。logo 读本插件 assets/ 下的 *1.png。

单独运行: python3 plugins/stock/plugin.py [--device IP] [--interval 7] [--dry-run] [--once]
"""
import os, sys, base64, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "stock"
NAME = "股票看板"
GROUP = "信息"
DESC = "美股看板：AAPL / MSFT / NVDA / GOOGL 轮播，显示实时价与公司 logo，涨绿跌红。"
DEFAULT_INTERVAL = 7
ITEMS = ["AAPL", "MSFT", "NVDA", "GOOGL"]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO_FILES = {"AAPL": "aapl1.png", "MSFT": "msft1.png", "NVDA": "nvda1.png", "GOOGL": "googl1.png"}
_logos = None


def get_logos():
    global _logos
    if _logos is None:
        _logos = {}
        for sym, fn in LOGO_FILES.items():
            p = os.path.join(ASSETS, fn)
            if os.path.exists(p):
                with open(p, "rb") as f:
                    _logos[sym] = "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return _logos


def get_quote(sym):
    try:
        req = urllib.request.Request(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=12) as r:
            m = json.load(r)["chart"]["result"][0]["meta"]
        return float(m["regularMarketPrice"]), float(m["chartPreviousClose"])
    except Exception:
        return None


def frame_for(sym, interval):
    q = get_quote(sym)
    if not q or q[0] <= 0:
        return None
    price, prev = q
    chg = (price - prev) / prev * 100 if prev > 0 else 0.0
    ps = f"{price:,.0f}" if price >= 1000 else f"{price:.1f}"
    color = "#00FF66" if chg >= 0 else "#FF3030"
    frame = {"duration": interval,
             "text": [{"content": ps, "fontHeight": 10, "x": 20, "y": 3, "color": color}]}
    logos = get_logos()
    if sym in logos:
        frame["image"] = [{"data": logos[sym], "position": [0, 0]}]
    return frame, f"{sym:6} {ps:>8}  {chg:+.1f}%"


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
