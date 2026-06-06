#!/usr/bin/env python3
"""pet — 像素宠物 -> 像素时钟 DIY "pet"（插件, macOS）

两种模式:
  cpu    — 随 CPU 负载切状态: 闲(<30%)打盹 IDLE / 中(<70%)散步 WALK / 高负载狂奔 RUN。
  random — 完全随机, 每隔 interval 秒换一个动作(含 jump/attack), 自由活动。
以循环 GIF 推送; cpu 模式下状态不变不重复推(GIF 在设备上自循环)。

素材: "FREE Cat 2D Pixel Art"(见 assets/License.txt, 可自由用于项目, 署名作者表敬意)。
GIF 由 build_pet.py 预生成(需 Pillow); 本运行时只读成品 GIF, 纯标准库。

单独运行: python3 plugins/pet/plugin.py [--device IP] [--interval 4] [--dry-run] [--once]
"""
import os, sys, base64, random, re, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pixbar_core as core

APP = "pet"
NAME = "像素宠物"
GROUP = "视觉"
DESC = "像素宠物（橘猫）：随 CPU 负载或完全随机切换动作——打盹、散步、狂奔。"
DEFAULT_INTERVAL = 4
ITEMS = ["idle", "walk", "run", "attack"]             # 原地循环动作; 供"推一次"预览
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
OPTIONS = [{
    "key": "mode", "label": "模式", "default": "cpu",
    "choices": [["cpu", "跟随 CPU 负载"], ["random", "完全随机"]],
}]
_cache = {}


def gif_data(state):
    if state not in _cache:
        with open(os.path.join(ASSETS, f"{state}.gif"), "rb") as f:
            _cache[state] = "data:image/gif;base64," + base64.b64encode(f.read()).decode()
    return _cache[state]


def get_cpu():
    try:
        out = subprocess.run(["top", "-l", "2", "-n", "0"], capture_output=True, text=True, timeout=15).stdout
        line = [l for l in out.splitlines() if "CPU usage" in l][-1]
        return int(round(100 - float(re.search(r"([\d.]+)%\s*idle", line).group(1))))
    except Exception:
        return None


def state_for_cpu(cpu):
    return "idle" if cpu < 30 else "walk" if cpu < 70 else "run"


def frame_for(state, interval):
    """供'推一次'/发现使用: 直接给某状态的一帧 GIF。"""
    if state not in ITEMS:
        state = "idle"
    frame = {"duration": interval, "image": [{"data": gif_data(state), "position": [0, 0]}]}
    return frame, f"pet -> {state}"


def _push_state(device, state, interval, log, dry_run, note):
    ts = time.strftime("%H:%M:%S")
    if dry_run:
        log(f"{ts}  {note} -> {state}  (would push)"); return
    try:
        core.push(device, APP, frame_for(state, interval)[0]); log(f"{ts}  {note} -> {state}")
    except Exception as e:
        log(f"  push fail: {e}")


def run_loop(device, interval, stop=None, log=print, dry_run=False, once=False, options=None):
    """mode=cpu: 按负载切状态, 变化才推; mode=random: 每轮随机换动作。options 实时读, 可热切换。"""
    options = options or {}
    cur = None
    while stop is None or not stop.is_set():
        mode = options.get("mode", "cpu")
        if mode == "random":
            state = random.choice([s for s in ITEMS if s != cur])     # 不与上一个重复
            _push_state(device, state, interval, log, dry_run, "random")
            cur = state
        else:
            cpu = get_cpu()
            if cpu is None:
                log("  cpu read fail")
            else:
                state = state_for_cpu(cpu)
                if state != cur:
                    _push_state(device, state, interval, log, dry_run, f"CPU {cpu:3d}%")
                    cur = state
                else:
                    log(f"{time.strftime('%H:%M:%S')}  CPU {cpu:3d}%  ({state})")
        if once:
            break
        if stop is not None:
            if stop.wait(interval):
                break
        else:
            time.sleep(interval)


if __name__ == "__main__":
    core.standalone(sys.modules[__name__])
