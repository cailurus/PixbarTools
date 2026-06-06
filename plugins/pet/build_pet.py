#!/usr/bin/env python3
"""build_pet.py — 一次性构建脚本(需 Pillow): 把猫 sprite 表转成 52x16 循环 GIF。

关键: 所有帧共用一个**全局纵向窗口**[最高顶, 最低底](跨全部动作), 映射到 16px 高。
这样最高的姿势(jump 起跳/attack)正好填满屏高、绝不裁顶, 站姿自然落底, jump 能真正升起。
横向按各状态自身内容居中。运行时 plugin.py 只读成品 GIF, 不依赖 Pillow。

  python3 plugins/pet/build_pet.py        # 重新生成 GIF + 自检 filmstrip.png
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "assets", "sprites")
OUT = os.path.join(HERE, "assets")
FW, FH = 80, 64
SCREEN_W, SCREEN_H = 52, 16
STATES = {                            # 状态: (文件, 每帧毫秒)
    "idle":   ("IDLE.png", 160),
    "walk":   ("WALK.png", 110),
    "run":    ("RUN.png", 80),
    "attack": ("ATTACK 1.png", 90),
    # 注: JUMP/RUNNING JUMP 是"腾空姿势"(原游戏靠引擎平移做升降), 原地循环只会抖, 16px 也放不下弧线 -> 不用
}


def frames_of(path):
    sheet = Image.open(path).convert("RGBA")
    n = sheet.width // FW
    return [sheet.crop((i * FW, 0, (i + 1) * FW, FH)) for i in range(n)]


def bbox(im):
    return im.split()[3].point(lambda v: 255 if v > 16 else 0).getbbox()


def compose(frame, x0, x1, vtop, vbot, scale):
    """裁 [x0,vtop,x1,vbot] 固定纵向窗→统一 scale 缩放→居中合成到 52x16 黑底。"""
    cat = frame.crop((x0, vtop, x1, vbot))
    nw, nh = max(1, round((x1 - x0) * scale)), max(1, round((vbot - vtop) * scale))
    cat = cat.resize((nw, nh), Image.NEAREST)
    canvas = Image.new("RGBA", (SCREEN_W, SCREEN_H), (0, 0, 0, 255))
    x = (SCREEN_W - nw) // 2
    y = SCREEN_H - nh                              # 窗口高≈16, 贴底; 顶部多出的空像素留黑
    canvas.paste(cat, (x, max(0, y)), cat)
    return canvas.convert("RGB")


def main():
    sheets = {st: frames_of(os.path.join(SPR, fn)) for st, (fn, _) in STATES.items()}
    allbb = [bbox(f) for fr in sheets.values() for f in fr if bbox(f)]
    vtop = min(b[1] for b in allbb)                # 跨全部动作: 最高的顶
    vbot = max(b[3] for b in allbb)                # 跨全部动作: 最低的底
    scale = SCREEN_H / (vbot - vtop)               # 让最高姿势正好填满 16px
    print(f"全局纵向窗 y=[{vtop},{vbot}] ({vbot-vtop}px) -> 16px  scale={scale:.3f}")

    # 胶片图: 每状态一行, 横排该状态全部帧, 标出屏幕边界
    S = 6
    maxframes = max(len(fr) for fr in sheets.values())
    film = Image.new("RGB", ((SCREEN_W + 1) * maxframes * S, SCREEN_H * len(STATES) * S), (40, 40, 40))

    for row, (state, (fn, ms)) in enumerate(STATES.items()):
        bbs = [bbox(f) for f in sheets[state] if bbox(f)]
        x0, x1 = min(b[0] for b in bbs), max(b[2] for b in bbs)   # 该状态横向窗
        frames = [compose(f, x0, x1, vtop, vbot, scale) for f in sheets[state]]
        gif = os.path.join(OUT, f"{state}.gif")
        frames[0].save(gif, save_all=True, append_images=frames[1:],
                       duration=ms, loop=0, disposal=2, optimize=False)
        # 检查顶行是否触顶(裁切迹象): 第 0 行有亮像素即可能被裁
        toprow = any(frames[k].getpixel((x, 0)) != (0, 0, 0) for k in range(len(frames)) for x in range(SCREEN_W))
        print(f"  {state:6} {len(frames)} 帧 @ {ms}ms -> {state}.gif   顶行有像素={toprow}")
        for k, fr in enumerate(frames):
            film.paste(fr.resize((SCREEN_W * S, SCREEN_H * S), Image.NEAREST), (k * (SCREEN_W + 1) * S, row * SCREEN_H * S))
    film.save(os.path.join(OUT, "filmstrip.png"))
    print("胶片自检图:", os.path.join(OUT, "filmstrip.png"))


if __name__ == "__main__":
    main()
