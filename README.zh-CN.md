<div align="center">

# PixDeck

**用一个本地网页应用,把实时数据、小游戏、氛围动效推送到你的 Ulanzi 像素时钟(TC002,52×16 RGB 点阵)上。无需刷固件。**

[English](./README.md) · 简体中文

<!-- 在这里放一张网页界面的截图,例如:
<img src="assets/screenshot.png" width="680" alt="PixDeck 网页界面">
-->

</div>

---

## 快速开始

需要 **Python 3**,以及一台和电脑在同一 Wi-Fi 下的 Pixbar / TC002。

```bash
git clone https://github.com/cailurus/PixDeck.git
cd PixDeck
python3 pixbar_panel.py
```

打开 **http://127.0.0.1:8000**,点齿轮填入时钟的 IP —— 之后重启也会记住。无需 `npm`、无需 `pip install`。

> 喜欢命令行?`python3 pixbar_panel.py --device <IP> --port 8000` 可以开机时就指定。

## 能往时钟上放什么

在网页里随手开关下面这些 —— 每一项都是一个小插件,把画面推送到设备:

- **信息** —— 美股、加密货币、实时天气、系统监控(CPU/内存/GPU/磁盘)、正在播放的曲目、Claude Code 会话状态
- **游戏**(AI 自动玩)—— 贪吃蛇、乒乓球、打砖块、吃豆人
- **视觉** —— 像素橘猫、星空穿梭、落沙、火焰、兰顿蚂蚁、自动走迷宫、像素鱼缸
- **工具** —— 把你输入的任意一句话滚动显示的留言板
- **定时** —— 整点播报、定时提醒、换歌播报

还有一个**画板**标签:一块 52×16 像素编辑器,可手绘、落文字,或载入并像素化一张 Logo,然后把画面直接推到时钟上。

## 工作原理

一个本地服务器(`pixbar_panel.py`,纯 Python 标准库)把每个插件各跑在一个线程里、托管网页应用、并转发设备的 HTTP API —— 全部绑定在 `127.0.0.1`。浏览器只跟这个本地服务器通信,再由它在局域网内连你的时钟。插件放在 `plugins/<名>/` 下、自动发现。

---

<div align="center">

*个人 / 学习用途项目,与 Ulanzi 无官方关联。*

</div>
