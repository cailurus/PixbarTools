#!/usr/bin/env python3
"""pixbar_panel.py — 像素时钟控制台（本地控制服务器, 纯标准库）

跑在 127.0.0.1: 自动发现 plugins/ 下所有插件, 用网页统一开关、看设备状态、手动推一帧。
浏览器只跟本服务器通信(同源), 服务器管线程 + 转发设备 API。

用法:
  python3 pixbar_panel.py                 # 启动后浏览器开 http://127.0.0.1:8000
  python3 pixbar_panel.py --device <IP> --port 8000
"""
import argparse, ipaddress, json, os, threading, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, quote

import pixbar_core as core

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIST = os.path.join(HERE, "web", "dist")
CONFIG_PATH = os.path.join(HERE, ".pixbar.json")          # 本地配置(设备 IP 等), 不入库


def load_device():
    """读取上次在界面里设置并记住的设备 IP; 没有则返回空串。"""
    try:
        with open(CONFIG_PATH) as f:
            return str(json.load(f).get("device", ""))
    except Exception:
        return ""


def save_device(ip):
    """把界面设置的设备 IP 写到本地配置, 重启后仍记得。"""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump({"device": ip}, f)
    except Exception:
        pass


def valid_device(s):
    """校验设备地址: 必须是私网 IPv4(可带 :端口)。服务器会拿这个地址去发请求, 限制到私网
    可挡住把它设成元数据(169.254.169.254)/环回/公网地址做 SSRF。合法则返回规范化串, 否则空串。"""
    s = (s or "").strip()
    if not s:
        return ""
    host, sep, port = s.partition(":")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return ""
    if ip.version != 4 or not ip.is_private or ip.is_loopback or ip.is_link_local:
        return ""
    if sep and (not port.isdigit() or not (1 <= int(port) <= 65535)):
        return ""
    return s
_ALL = core.discover(os.path.join(HERE, "plugins"))
PLUGINS = {m.APP: m for m in _ALL if not getattr(m, "ATTACH", False)}        # 主信息流插件
ATTACH_TYPES = {m.APP: m for m in _ALL if getattr(m, "ATTACH", False)}       # 附属推送类型(模板)


def apply_option(optspec, options, key, value):
    """按 optspec 校验并写入一个选项。支持 type=text / number / 默认下拉。成功返回该选项规格, 否则 None。"""
    for o in optspec:
        if o["key"] != key:
            continue
        t = o.get("type")
        if t in ("text", "search"):                   # search: 存选中项的值串(lat|lon|显示名)
            options[key] = str(value)[:300]
        elif t == "number":
            try:
                v = int(float(value))
            except Exception:
                return None
            if o.get("min") is not None:
                v = max(o["min"], v)
            if o.get("max") is not None:
                v = min(o["max"], v)
            options[key] = v
        elif value in [c[0] for c in o.get("choices", [])]:
            options[key] = value
        else:
            return None
        return o
    return None


class Runner:
    """管理一个插件的后台线程: 开/关 + 环形日志缓冲。"""
    def __init__(self, mod):
        self.mod = mod
        self.thread = None
        self.stop = None
        self.active = False                 # 用户意图(开/关), UI 以此为准
        self.interval = getattr(mod, "DEFAULT_INTERVAL", 5)
        self.optspec = getattr(mod, "OPTIONS", [])
        self.options = {o["key"]: o["default"] for o in self.optspec}   # 当前选项(线程内实时读)
        self.log = []
        self.lock = threading.Lock()

    def set_option(self, key, value):
        o = apply_option(self.optspec, self.options, key, value)
        if not o:
            return False
        self._emit(f"{time.strftime('%H:%M:%S')}  {o['label']} = {self.options[key]}")
        return True

    def _emit(self, line):
        with self.lock:
            self.log.append(line)
            del self.log[:-30]

    def running(self):
        return self.active

    def start(self, device, interval):
        if self.active:
            return
        self.interval = interval
        self.active = True
        self.stop = threading.Event()
        self._emit(f"{time.strftime('%H:%M:%S')}  started ({device}, {interval}s)")
        loop = core.loop_callable(self.mod)
        self.thread = threading.Thread(
            target=loop,
            kwargs=dict(device=device, interval=interval, stop=self.stop, log=self._emit, options=self.options),
            daemon=True)
        self.thread.start()

    def set_interval(self, iv, device=None):
        """设置轮播间隔并持久化。运行中则软重启线程(不删设备组件, 无空白)以套用新间隔。"""
        iv = max(1, int(iv))
        self.interval = iv
        self._emit(f"{time.strftime('%H:%M:%S')}  间隔 = {iv}s")
        if self.active and device is not None:
            if self.stop:
                self.stop.set()
            if self.thread:
                self.thread.join(timeout=3)
            self.active = False
            self.start(device, iv)

    def stop_run(self, device=None):
        self.active = False
        if self.stop:
            self.stop.set()
        if self.thread:
            self.thread.join(timeout=3)               # 先等线程退出, 防止它再推一帧重建组件
        core.clear_preempt(self.mod.APP)               # 解除附属对本组件的抢占
        ts = time.strftime("%H:%M:%S")
        if device:                                     # 再从设备删除该 DIY 组件(空 body=删除), 不残留末帧
            try:
                core.push(device, self.mod.APP, {}, force=True)   # force: 即便正被抢占也要删掉
                self._emit(f"{ts}  stopped & removed from device")
            except Exception as e:
                self._emit(f"{ts}  stopped (device remove fail: {e})")
        else:
            self._emit(f"{ts}  stopped")

    def push_once(self, device, idx):
        items = self.mod.ITEMS
        item = items[idx % len(items)]
        res = self.mod.frame_for(item, self.interval)
        ts = time.strftime("%H:%M:%S")
        if not res:
            self._emit(f"{ts}  no data: {item}"); return
        try:
            core.push(device, self.mod.APP, res[0]); self._emit(f"{ts}  (once) {res[1]}")
        except Exception as e:
            self._emit(f"{ts}  push fail: {e}")

    def snapshot(self):
        with self.lock:
            return {"name": getattr(self.mod, "NAME", self.mod.APP),
                    "group": getattr(self.mod, "GROUP", "其他"),
                    "desc": getattr(self.mod, "DESC", ""),
                    "running": self.running(), "interval": self.interval,
                    "optspec": self.optspec, "options": dict(self.options), "log": list(self.log)}


RUNNERS = {app: Runner(mod) for app, mod in PLUGINS.items()}
_push_idx = {app: 0 for app in PLUGINS}


class Attachment:
    """一个附属推送的挂载实例: 附属类型 + 宿主 + 配置, 自带循环线程。"""
    def __init__(self, aid, mod, host):
        self.id = aid
        self.mod = mod                  # 附属类型模块
        self.host = host                # 宿主插件 APP 名
        self.optspec = getattr(mod, "OPTIONS", [])
        self.options = {o["key"]: o["default"] for o in self.optspec}
        self.active = False
        self.thread = None
        self.stop = None
        self.log = []
        self.lock = threading.Lock()

    def _emit(self, line):
        with self.lock:
            self.log.append(line)
            del self.log[:-30]

    def set_option(self, key, value):
        o = apply_option(self.optspec, self.options, key, value)
        if not o:
            return False
        self._emit(f"{time.strftime('%H:%M:%S')}  {o['label']} = {self.options[key]}")
        return True

    def running(self):
        return self.active

    def start(self, device):
        if self.active:
            return
        loop = getattr(self.mod, "attach_loop", None)
        if loop is None:                # 附属类型必须提供 attach_loop
            self._emit(f"{time.strftime('%H:%M:%S')}  错误: 附属类型缺少 attach_loop")
            return
        self.active = True
        self.stop = threading.Event()
        self._emit(f"{time.strftime('%H:%M:%S')}  started -> 宿主 {self.host}")

        def inject(frame, duration):    # 只在宿主运行时插播; 设备出错也不让线程挂掉
            hr = RUNNERS.get(self.host)
            if not hr or not hr.running():
                self._emit(f"{time.strftime('%H:%M:%S')}  跳过(宿主 {self.host} 未运行)")
                return
            try:
                core.inject(device, self.host, frame, duration)
            except Exception as e:
                self._emit(f"{time.strftime('%H:%M:%S')}  push fail: {e}")

        self.thread = threading.Thread(
            target=loop,
            kwargs=dict(device=device, host=self.host, options=self.options,
                        stop=self.stop, log=self._emit, inject=inject),
            daemon=True)
        self.thread.start()

    def stop_run(self):
        self.active = False
        if self.stop:
            self.stop.set()
        self._emit(f"{time.strftime('%H:%M:%S')}  stopped")

    def snapshot(self):
        with self.lock:
            return {"id": self.id, "type": self.mod.APP,
                    "typeName": getattr(self.mod, "NAME", self.mod.APP),
                    "host": self.host, "running": self.running(),
                    "optspec": self.optspec, "options": dict(self.options), "log": list(self.log)}


ATTACHMENTS = {}                        # id -> Attachment
_attach_seq = [0]
STATE_LOCK = threading.Lock()           # 保护跨请求/线程共享的 ATTACHMENTS / _attach_seq / _push_idx
_pushonce_at = {}                       # app -> 最近一次"推一次"的 monotonic(短时豁免对账)
PUSHONCE_GRACE = 30                     # 推一次后保留组件的秒数


def attach_types_info():
    return [{"type": m.APP, "name": getattr(m, "NAME", m.APP), "desc": getattr(m, "DESC", "")}
            for m in ATTACH_TYPES.values()]


def reconcile(device, apps):
    """删除设备上'未运行且非近期预览'的本工具组件, 使 DIY 组件始终 = 真正开着的插件。
    返回对账后仍在设备上的组件名列表。"""
    now = time.monotonic()
    kept = []
    for name in apps:
        stale = (name in PLUGINS and not RUNNERS[name].running()
                 and now - _pushonce_at.get(name, 0) > PUSHONCE_GRACE)
        if stale:
            try:
                core.push(device, name, {}, force=True)
                continue
            except Exception:
                pass
        kept.append(name)
    return kept


def geocode_search(q):
    """城市搜索: 中文自动转拼音(open-meteo 大城市主名是拼音, 直接搜中文只匹配到同名小地方),
    保留 open-meteo 的相关性排序(大城市通常排第一), 仅去重。
    需要 pypinyin 才能用中文搜大城市(可选: pip install pypinyin); 没装则退回原文搜索。"""
    q = (q or "").strip()
    if not q:
        return []
    name = q
    if any("一" <= c <= "鿿" for c in q):       # 含中文 -> 转拼音
        try:
            from pypinyin import lazy_pinyin
            name = "".join(lazy_pinyin(q))
        except Exception:
            pass
    try:
        g = json.load(urllib.request.urlopen(
            f"https://geocoding-api.open-meteo.com/v1/search?name={quote(name)}&count=20&language=zh", timeout=6))
    except Exception:
        return []
    # 只保留县级市以上: GeoNames 行政驻地(首都/省会/地级/县级)或人口>=3万; 丢掉村镇/机场等
    keep_codes = {"PPLC", "PPLA", "PPLA2", "PPLA3", "PPLG"}
    out, seen = [], set()
    for r in g.get("results", []):
        if r.get("feature_code") not in keep_codes and (r.get("population") or 0) < 30000:
            continue
        disp = ", ".join(x for x in (r.get("name"), r.get("admin1"), r.get("country")) if x)
        if disp in seen:
            continue
        seen.add(disp)
        out.append({"label": disp, "value": f"{r['latitude']}|{r['longitude']}|{disp}"})
    return out[:6]


def device_get(device, path, timeout=3):
    try:
        with urllib.request.urlopen(f"http://{device}{path}", timeout=timeout) as r:
            return json.load(r)
    except Exception:
        return None


STATIC_TYPES = {".js": "application/javascript", ".css": "text/css",
                ".png": "image/png", ".html": "text/html; charset=utf-8",
                ".svg": "image/svg+xml", ".woff2": "font/woff2",
                ".json": "application/json", ".map": "application/json", ".ico": "image/x-icon"}


def device_status(device):
    base = device_get(device, "/getBase")
    return {
        "online": base is not None,
        "base": base or {},
        "apps": device_get(device, "/api/customList") or {},
        "config": device_get(device, "/getConfig") or {},
    }


class Handler(BaseHTTPRequestHandler):
    device = ""                          # 设备 IP: 启动时从配置载入, 或在界面齿轮里设置

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass

    def _host_ok(self):
        """只接受 Host 指向本机的请求。防 DNS-rebinding: 即便恶意域名解析到 127.0.0.1,
        浏览器仍会带上该域名作 Host, 这里据此拒绝, 不让外部网页驱动本地 API。"""
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        return host in ("", "127.0.0.1", "localhost", "::1")

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, json.dumps({"error": "forbidden host"}))
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            with open(os.path.join(WEB_DIST, "index.html"), "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")
        if u.path == "/api/status":
            st = device_status(Handler.device)
            if st.get("online"):                       # 对账: 清掉未运行的残留组件
                apps = (st.get("apps") or {}).get("apps", [])
                st["apps"]["apps"] = reconcile(Handler.device, apps)
            st["device"] = Handler.device
            st["order"] = list(RUNNERS.keys())
            st["runners"] = {n: r.snapshot() for n, r in RUNNERS.items()}
            st["attachTypes"] = attach_types_info()
            with STATE_LOCK:                       # 防与并发的 attach 增删争用 → "dict changed size"
                att_items = list(ATTACHMENTS.items())
            st["attachments"] = {aid: a.snapshot() for aid, a in att_items}
            return self._send(200, json.dumps(st))
        if u.path == "/api/geocode":                  # 城市搜索(中文转拼音 + 按人口排序 + 去重)
            q = (parse_qs(u.query).get("q") or [""])[0]
            return self._send(200, json.dumps({"results": geocode_search(q)}))
        # SPA 构建产物(/assets/* 等), 仅从 web/dist 服务
        rel = u.path.lstrip("/")
        ext = os.path.splitext(rel)[1]
        if rel and ".." not in rel and ext in STATIC_TYPES:
            root = os.path.realpath(WEB_DIST)
            fp = os.path.realpath(os.path.join(WEB_DIST, rel))
            if os.path.isfile(fp) and os.path.commonpath([fp, root]) == root:
                with open(fp, "rb") as f:
                    return self._send(200, f.read(), STATIC_TYPES[ext])
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if not self._host_ok():
            return self._send(403, json.dumps({"error": "forbidden host"}))
        u = urlparse(self.path)
        q = parse_qs(u.query)
        app = (q.get("app") or [""])[0]
        if u.path == "/api/device":
            cand = valid_device((q.get("ip") or [""])[0])
            if not cand:
                return self._send(400, json.dumps({"error": "需要私网 IPv4 地址(可带端口), 如 192.168.1.50"}))
            Handler.device = cand
            save_device(cand)                     # 记住, 重启后仍生效
            return self._send(200, json.dumps({"device": cand}))
        # ---- 画板整屏推送: body 为 JSON {pixels:[832], duration?} ----
        if u.path == "/api/canvas/push":
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n <= 0 or n > 65536:                 # 整屏 832 像素 JSON 远小于此; 防空体/超大体
                    raise ValueError("bad length")
                payload = json.loads(self.rfile.read(n))
            except Exception:
                return self._send(400, json.dumps({"ok": False, "error": "bad json"}))
            pixels = payload.get("pixels")
            if not isinstance(pixels, list) or len(pixels) != 52 * 16:
                return self._send(400, json.dumps({"ok": False, "error": "pixels must be length 832"}))
            try:
                flat = [int(p) & 0xFFFFFF for p in pixels]
                duration = max(1, min(300, int(float(payload.get("duration") or 10))))  # 钳到 1..300s
            except Exception:
                return self._send(400, json.dumps({"ok": False, "error": "bad pixel/duration value"}))
            frame = core.bitmap_frame(flat, w=52, h=16, duration=duration)
            try:
                core.push(Handler.device, "canvas", frame, force=True)
                return self._send(200, json.dumps({"ok": True}))
            except Exception as e:
                return self._send(200, json.dumps({"ok": False, "error": str(e)}))
        # ---- 附属推送挂载 ----
        if u.path == "/api/attach/add":
            host = (q.get("host") or [""])[0]; atype = (q.get("type") or [""])[0]
            if host not in RUNNERS or atype not in ATTACH_TYPES:
                return self._send(400, json.dumps({"error": "bad host/type"}))
            with STATE_LOCK:
                _attach_seq[0] += 1; aid = f"{atype}-{_attach_seq[0]}"
                ATTACHMENTS[aid] = Attachment(aid, ATTACH_TYPES[atype], host)
                snap = ATTACHMENTS[aid].snapshot()
            return self._send(200, json.dumps(snap))
        if u.path in ("/api/attach/remove", "/api/attach/toggle", "/api/attach/option"):
            a = ATTACHMENTS.get((q.get("id") or [""])[0])
            if not a:
                return self._send(400, json.dumps({"error": "unknown attachment"}))
            if u.path == "/api/attach/remove":
                a.stop_run()
                with STATE_LOCK:
                    ATTACHMENTS.pop(a.id, None)
                return self._send(200, json.dumps({"ok": True}))
            if u.path == "/api/attach/toggle":
                on = (q.get("on") or ["0"])[0] == "1"
                a.start(Handler.device) if on else a.stop_run()
                return self._send(200, json.dumps(a.snapshot()))
            key = (q.get("key") or [""])[0]; value = (q.get("value") or [""])[0]
            a.set_option(key, value)
            return self._send(200, json.dumps(a.snapshot()))
        if app not in RUNNERS:
            return self._send(400, json.dumps({"error": "unknown app"}))
        r = RUNNERS[app]
        if u.path == "/api/toggle":
            on = (q.get("on") or ["0"])[0] == "1"
            try:
                interval = int((q.get("interval") or [str(r.interval)])[0])
            except (ValueError, TypeError):
                return self._send(400, json.dumps({"error": "bad interval"}))
            interval = max(1, min(86400, interval))    # 钳到合理范围, 防异常值
            r.start(Handler.device, interval) if on else r.stop_run(Handler.device)
            return self._send(200, json.dumps(r.snapshot()))
        if u.path == "/api/interval":
            try:
                iv = int(float((q.get("interval") or ["5"])[0]))
            except (ValueError, TypeError):
                return self._send(400, json.dumps({"error": "bad interval"}))
            r.set_interval(max(1, min(86400, iv)), Handler.device)
            return self._send(200, json.dumps(r.snapshot()))
        if u.path == "/api/pushonce":
            with STATE_LOCK:
                idx = _push_idx[app]; _push_idx[app] = idx + 1
            r.push_once(Handler.device, idx)
            _pushonce_at[app] = time.monotonic()       # 短时豁免对账, 让预览帧留得住
            return self._send(200, json.dumps(r.snapshot()))
        if u.path == "/api/option":
            key = (q.get("key") or [""])[0]; value = (q.get("value") or [""])[0]
            r.set_option(key, value)
            return self._send(200, json.dumps(r.snapshot()))
        return self._send(404, json.dumps({"error": "not found"}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default=None, help="设备 IP(可选; 不填则用上次界面里设置的, 或留空在网页里填)")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    raw = args.device if args.device is not None else load_device()
    Handler.device = valid_device(raw)       # 私网 IPv4 校验; 非法则视为未设置
    if raw and not Handler.device:
        print(f"警告: 设备地址 {raw!r} 不是有效私网 IPv4, 已忽略 — 请在网页里填")
    if args.device is not None and Handler.device:
        save_device(Handler.device)          # 命令行显式指定且合法时也记住
    # 启动时清掉设备上本工具插件的残留组件(都处于"未运行"状态), 使 DIY 组件显示与开关一致
    if Handler.device:
        cl = device_get(Handler.device, "/api/customList")
        for name in (cl or {}).get("apps", []):
            if name in PLUGINS:
                try:
                    core.push(Handler.device, name, {}, force=True)
                except Exception:
                    pass
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"pixbar_panel -> http://127.0.0.1:{args.port}  (device {Handler.device or '未设置 — 在网页里填'})")
    print(f"plugins: {', '.join(RUNNERS) or '(none)'}")
    print("Ctrl+C 停止")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        for r in RUNNERS.values():
            r.stop_run()
        print("\nstopped")


if __name__ == "__main__":
    main()
