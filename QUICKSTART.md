# 快速使用指南

## 📊 GPX HUD 叠加视频生成工具

这个工具可以将 GPX 徒步数据生成带透明通道的 HUD 视频，直接叠加到 vlog 上。

---

## 🚀 快速开始

### 1️⃣ 先查看数据信息
```bash
python analyze_gpx.py
```

输出示例：
- 总数据点数: 14164
- 开始时间: 2025-10-05T01:58:19Z
- 结束时间: 2025-10-05T06:07:41Z  
- 总时长: 4:09:22
- 海拔范围: 1176.8m - 1963.4m

### 2️⃣ 生成 HUD 视频

**方法 A: 按时间范围**
```bash
python gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 02:15:00 -o my_hud.mov
```

**方法 B: 按数据点索引**
```bash
python gpx_hud_overlay.py hike.gpx -s 0 -e 1000 -o my_hud.mov
```

**方法 C: 生成完整视频**
```bash
python gpx_hud_overlay.py hike.gpx -o overlay_full.mov
```

---

## 📺 HUD 显示内容

生成的视频下方显示 4 项实时信息：
- **HR**: 心率（BPM）
- **ALT**: 海拔高度（米）
- **DIST**: 累计距离（公里）
- **TIME**: 运动时间（HH:MM:SS）

---

## 🎬 在视频编辑软件中使用

### Final Cut Pro / DaVinci Resolve
1. 导入主视频到主轨道
2. 将 `my_hud.mov` 导入为上层轨道
3. 自动识别 Alpha 通道，下方视频会显示在透明区域

### Adobe Premiere / Davinci Resolve
1. 将 `my_hud.mov` 放在时间线的上方
2. 上层的黑色背景会自动变成透明（Alpha 混合）

---

## ⚙️ 常用参数

| 参数 | 说明 | 例子 |
|------|------|------|
| `-st` / `--start-time` | 开始时间 | `-st 02:30:00` |
| `-et` / `--end-time` | 结束时间 | `-et 03:00:00` |
| `-s` / `--start` | 起始数据点 | `-s 1000` |
| `-e` / `--end` | 结束数据点 | `-e 5000` |
| `-w` / `--width` | 视频宽度 | `-w 1920` |
| `--height` | 视频高度 | `--height 1080` |
| `-f` / `--fps` | 帧率 | `-f 30` |
| `--real-time` | 生成视频时长与实际徒步时长相同 | `--real-time` |
| `--no-map` | 隐藏路线地图 | `--no-map` |
| `-o` / `--output` | 输出文件名 | `-o my_hud.mov` |

---

## 🎬 特殊功能

### 实时时长模式 `--real-time`

生成的视频时长会与实际徒步时长相同。脚本会自动计算适当的帧率。

```bash
# 生成完整徒步的视频，时长 = 4 小时 9 分
python gpx_hud_overlay.py hike.gpx --real-time -o full_realtime.mov

# 生成特定时间段，视频时长等于实际时长
python gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 03:00:00 --real-time -o segment_realtime.mov
```

**工作原理**: 脚本计算选中数据点的实际时间差，然后自动调整 fps：
- 500 个数据点，实际时长 500 秒 → fps = 1.0
- 14164 个数据点，实际时长 15000 秒 → fps ≈ 0.94

---

## 📝 示例命令

### 生成 10 分钟的爬升段
```bash
python gpx_hud_overlay.py hike.gpx -st 02:30:00 -et 02:40:00 -o climb.mov
```

### 生成 720p 分辨率的 HUD
```bash
python gpx_hud_overlay.py hike.gpx -w 1280 --height 720 -o hud_720p.mov
```

### 使用 24fps（电影质感）
```bash
python gpx_hud_overlay.py hike.gpx -f 24 -o hud_cinema.mov
```

### 生成前 500 个数据点
```bash
python gpx_hud_overlay.py hike.gpx -e 500 -o start_segment.mov
```

### 使用实时时长（视频时长=实际时长）
```bash
python gpx_hud_overlay.py hike.gpx --real-time -o full_realtime.mov
```

### 特定时间段的实时视频
```bash
python gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 03:00:00 --real-time -o hour_realtime.mov
```

---

## 🔧 性能优化

如果生成太慢，可以：

1. **降低分辨率**
```bash
python gpx_hud_overlay.py hike.gpx -w 1280 --height 720 -o output.mov
```

2. **只生成需要的部分**
```bash
python gpx_hud_overlay.py hike.gpx -s 1000 -e 3000 -o segment.mov
```

3. **降低帧率**
```bash
python gpx_hud_overlay.py hike.gpx -f 15 -o output.mov
```

---

## 📐 数据点到时间的转换

根据 `analyze_gpx.py` 的输出：
- 每 120 个数据点 ≈ 2 分钟
- 每个数据点 ≈ 1 秒钟

所以如果要生成从 2:30:00 到 2:40:00 的 10 分钟视频：
- 查看分析结果找到这两个时刻对应的数据点索引
- 使用 `-s` 和 `-e` 参数

---

## 💡 工作流示例

```bash
# 1. 分析数据
python analyze_gpx.py

# 2. 生成想要的时间段
python gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 02:10:00 -o seg1.mov
python gpx_hud_overlay.py hike.gpx -st 03:00:00 -et 03:10:00 -o seg2.mov

# 3. 在视频编辑软件中
# - 将主视频导入
# - 将 seg1.mov 和 seg2.mov 作为上层轨道
# - 自动处理透明度，导出视频
```

---

## ❓ 常见问题

**Q: 如何自定义 HUD 样式？**
A: 编辑 `gpx_hud_overlay.py` 中的 `HUDOverlayGenerator` 类

**Q: 为什么心率显示为 None？**
A: 这个 GPX 文件没有记录心率数据

**Q: 可以改变 HUD 的位置吗？**
A: 可以，编辑 `create_frame()` 方法中的 `putText()` 坐标

**Q: 视频太大了怎么办？**
A: 使用 ffmpeg 压缩或降低分辨率

---

## 📂 文件说明

- `gpx_hud_overlay.py` - 主脚本
- `analyze_gpx.py` - 数据分析工具
- `CONFIG.md` - 详细配置文档
- `hike.gpx` - 原始 GPX 数据文件

---

**创建时间**: 2025-12-21
**工具**: GPX HUD Overlay Generator
