#!/usr/bin/env python3
"""pixbar_core.py — 像素时钟插件框架（纯标准库）

插件放在 plugins/<名>/plugin.py, 控制台自动发现。分两类:

【主信息流插件】占一个设备组件、持续循环。约定:
  APP   NAME   GROUP(信息/工具/游戏/视觉)   DESC(一句话说明)
  DEFAULT_INTERVAL : int   ITEMS : list(轮播项)
  frame_for(item, interval) -> (frame_dict, logline) | None
  run_loop(device, interval, stop, log, dry_run, once, options)  # 可选; 不提供则用本模块默认循环
  可选 OPTIONS(面板下拉/文本/数字); 末尾加 if __name__=='__main__': core.standalone(...) 可单独跑。

【附属推送插件】不占组件、必须挂在某个主信息流上(由用户在宿主详情里添加)。约定:
  ATTACH = True            # 标记为附属类型(不在左侧列表单独出现)
  APP   NAME   DESC
  OPTIONS                  # 配置项(间隔/文字/颜色等)
  attach_loop(device, host, options, stop, log, inject):
      # 自己决定何时触发(间隔/整点/事件), 到点调 inject(frame, hold_seconds)
      # inject 由框架提供: 抢占宿主组件 hold 秒并强制推一帧; 宿主未运行时自动跳过。
      # stop 是 threading.Event; 用 stop.wait(秒) 做可中断的等待。
  画面用 core.text_frame(core.ascii_upper(s), color, hold) 构造; 颜色用 core.color_option(默认色)。

参考: 主流看 plugins/stock 或 sysmon; 附属看 plugins/reminder、hourly、songchange。
"""
import json, os, threading, time, unicodedata, importlib.util, urllib.request

# ---- 组件抢占 (附属推送插件用) ----
# 附属插件触发时"抢占"宿主组件 N 秒: 这期间宿主对该组件的 push 自动丢弃, 显示附属内容;
# 过期后宿主下一帧自然把画面盖回去。force=True 的 push (附属注入) 不受抢占影响。
_preempt = {}                       # app -> 抢占到期的 monotonic 时刻
_preempt_lock = threading.Lock()


def push(device, app, frame, force=False):
    """把一帧画面 POST 到设备 DIY 组件 app。app 正被附属抢占且非 force 时, 丢弃本次推送。"""
    if not force:
        with _preempt_lock:
            if _preempt.get(app, 0) > time.monotonic():
                return
    body = json.dumps(frame).encode()
    req = urllib.request.Request(f"http://{device}/api/custom?name={app}",
                                 data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()


def inject(device, host, frame, duration):
    """附属推送: 抢占宿主组件 duration 秒并强制推一帧。期间宿主的普通 push 被丢弃。"""
    with _preempt_lock:
        _preempt[host] = time.monotonic() + max(1, duration)
    push(device, host, frame, force=True)


def clear_preempt(app):
    """解除对组件的抢占(宿主停止时调用, 避免残留抑制)。"""
    with _preempt_lock:
        _preempt.pop(app, None)


def bitmap_frame(pixels, w=52, h=16, duration=5):
    """整屏位图帧: pixels 为行优先长度 w*h 的十进制 0x00RRGGBB 数组, 用一条 db 指令渲染。
    供视觉型插件(贪吃蛇/球类/粒子等)复用, 避免每个插件重复拼 db。"""
    return {"duration": duration, "draw": [{"db": [0, 0, w, h, pixels]}]}


def ascii_upper(s):
    """设备字体只支持 ASCII 且小写有缺字: 重音音译 + 仅保留可见 ASCII + 转大写。"""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return "".join(c for c in s if 0x20 <= ord(c) <= 0x7E).strip()


def color_option(default="#3EE08A", key="color", label="颜色"):
    """标准颜色下拉选项(供附属插件复用, 统一一处调色板)。"""
    return {"key": key, "label": label, "default": default, "choices": [
        ["#FFFFFF", "白"], ["#3EE08A", "绿"], ["#FFD000", "黄"], ["#FF5A52", "红"],
        ["#4285F4", "蓝"], ["#FF6400", "橙"], ["#00E5FF", "青"]]}


def text_frame(text, color="#FFFFFF", duration=8, w=52, h=16, fallback=" "):
    """一句文字帧: 放得下则居中, 放不下则左对齐(设备不滚动)。text 需已是 ASCII。供附属插件复用。"""
    t = text or fallback
    el = {"content": t, "fontHeight": 10, "y": 3, "color": color}
    if len(t) * 6 <= w:
        el.update({"x": -1000, "align": "center", "rect": [0, 0, w, h]})
    else:
        el.update({"x": 0, "rect": [0, 0, w, h]})
    return {"duration": duration, "text": [el]}


def run_loop(plugin, device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """默认循环: 轮播 plugin.ITEMS, 每项调 frame_for 渲染并推送。可被 stop 打断。
    options 供自带 run_loop 的插件使用; 默认循环忽略它。"""
    items = plugin.ITEMS
    i = 0
    while stop is None or not stop.is_set():
        item = items[i % len(items)]
        i += 1
        res = plugin.frame_for(item, interval)
        ts = time.strftime("%H:%M:%S")
        if res:
            frame, line = res
            if dry_run:
                log(f"{ts}  {line}   {json.dumps(frame)}")
            else:
                try:
                    push(device, plugin.APP, frame); log(f"{ts}  {line}")
                except Exception as e:
                    log(f"  push fail: {e}")
        else:
            log(f"  no data: {item}")
        if once and i >= len(items):
            break
        if stop is not None:
            if stop.wait(interval):
                break
        else:
            time.sleep(interval)


def loop_callable(plugin):
    """返回该插件的循环函数(自带 run_loop 优先, 否则默认)。签名统一为关键字参数。"""
    custom = getattr(plugin, "run_loop", None)
    if custom:
        return custom
    return lambda **kw: run_loop(plugin, **kw)


def discover(plugins_dir):
    """发现插件: 每个插件是 plugins/<名>/ 文件夹, 入口为其中的 plugin.py。
    文件夹可同时存放该插件自己的 assets/。忽略下划线开头的目录。"""
    mods = []
    if not os.path.isdir(plugins_dir):
        return mods
    for name in sorted(os.listdir(plugins_dir)):
        if name.startswith("_") or name.startswith("."):
            continue
        entry = os.path.join(plugins_dir, name, "plugin.py")
        if not os.path.isfile(entry):
            continue
        spec = importlib.util.spec_from_file_location(f"plugin_{name}", entry)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception as e:
            print(f"  [plugin skip] {name}: {e}")
            continue
        if hasattr(m, "APP") and (hasattr(m, "frame_for") or getattr(m, "ATTACH", False)):
            mods.append(m)
    return mods


def standalone(plugin):
    """供插件 `if __name__=='__main__'` 调用: 命令行单独运行该插件。"""
    import argparse, sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="", help="设备 IP(推送到设备时必填; 配合 --dry-run 可不填)")
    ap.add_argument("--interval", type=int, default=plugin.DEFAULT_INTERVAL)
    ap.add_argument("--dry-run", action="store_true", help="只取数+打印, 不推设备")
    ap.add_argument("--once", action="store_true", help="每项各一轮后退出")
    a = ap.parse_args()
    if not a.device and not a.dry_run:
        print("请用 --device <设备IP> 指定像素时钟地址(或加 --dry-run 只打印不推送)")
        return
    print(f"{plugin.APP} -> {a.device or '(dry-run)'}  interval {a.interval}s{'  [dry-run]' if a.dry_run else ''}")
    opts = {o["key"]: o["default"] for o in getattr(plugin, "OPTIONS", [])}
    fn = loop_callable(plugin)
    try:
        fn(device=a.device, interval=a.interval, log=print, dry_run=a.dry_run, once=a.once, options=opts)
    except KeyboardInterrupt:
        print("\nstopped")
