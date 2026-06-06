#!/usr/bin/env python3
"""crypto — 加密货币行情 -> 像素时钟 DIY "crypto"（插件）

BTC/ETH 轮播: 币种标签(白) + 价格(紧凑, >=1万显示 xx.xK) + 24h 涨绿跌红。
数据: Binance 24hr ticker(无需 Key), 失败回退 Coinbase 现价(无涨跌)。

单独运行: python3 plugins/crypto/plugin.py [--device IP] [--interval 8] [--dry-run] [--once]
"""
import os, sys, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "crypto"
NAME = "加密货币"
GROUP = "信息"
DESC = "加密货币行情：BTC / ETH 实时价格与 24 小时涨跌，涨绿跌红，轮播切换。"
DEFAULT_INTERVAL = 8
ITEMS = ["BTC", "ETH"]
UA = "Mozilla/5.0"


def _get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=10))


def get_price(sym):
    """返回 (price, change24h%) 或 None。"""
    try:
        d = _get(f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}USDT")
        return float(d["lastPrice"]), float(d["priceChangePercent"])
    except Exception:
        pass
    try:  # 回退: Coinbase 现价(无 24h 涨跌)
        d = _get(f"https://api.coinbase.com/v2/prices/{sym}-USD/spot")
        return float(d["data"]["amount"]), 0.0
    except Exception:
        return None


def fmt_price(v):
    if v >= 10000:
        return f"{v/1000:.1f}K"      # 63.5K
    if v >= 1000:
        return f"{v:.0f}"            # 1770
    return f"{v:.1f}"               # 不足千的小币种


def frame_for(sym, interval):
    r = get_price(sym)
    if not r:
        return None
    price, chg = r
    color = "#00FF66" if chg >= 0 else "#FF3030"
    ps = fmt_price(price)
    frame = {
        "duration": interval,
        "text": [
            {"content": sym, "fontHeight": 10, "x": 1, "y": 3, "color": "#FFFFFF"},
            {"content": ps, "fontHeight": 10, "x": -1000, "y": 3,
             "align": "right", "rect": [0, 0, 52, 16], "color": color},
        ],
    }
    return frame, f"{sym:4} {ps:>8}  {chg:+.1f}%"


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
