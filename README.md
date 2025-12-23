# GPX HUD 叠加视频生成工具 - 完整说明

## 项目概述

这是一个 Python 工具，可以从 GPX 徒步数据文件中提取心率、海拔、距离等信息，生成带 Alpha 透明通道的 HUD（抬头显示）叠加视频，用于与 vlog 视频合成。

---

## 🛠️ 安装依赖

### Mac 用户
```bash
# 安装 Python 依赖
pip3 install opencv-python numpy

# 安装 ffmpeg
brew install ffmpeg
```

### Linux 用户
```bash
pip install opencv-python numpy
sudo apt-get install ffmpeg
```

### Windows 用户
```bash
pip install opencv-python numpy
# 从 https://ffmpeg.org/download.html 下载安装 ffmpeg
```

---

## 📊 文件说明

### 脚本文件
- **`gpx_hud_overlay.py`** - 主脚本，生成 HUD 视频
- **`analyze_gpx.py`** - 数据分析工具，查看 GPX 数据范围和统计
- **`find_summit.py`** - 找到最高海拔点及其前后 200 米的片段参数

### 数据文件
- **`hike.gpx`** - GPX 徒步数据文件

### 文档
- **`QUICKSTART.md`** - 快速开始指南

---

## 🎯 工作流程

### 第 1 步：分析数据
```bash
python3 analyze_gpx.py
```

这会显示：
- 总数据点数和总时长
- 海拔统计（最低、最高、平均）
- 心率统计（如果有的话）
- 时间范围索引参考表

### 第 1.5 步：找到最高登顶点（可选）

如果你想生成最高海拔点附近的 HUD 视频，可以使用 `find_summit.py`：

```bash
python3 find_summit.py
```

**输出示例**：
```
总数据点数: 14164

最高海拔点:
  海拔: 1963.4 米
  数据点索引: 6591
  时间: 2025-10-05T03:48:13Z
  累计距离: 3.84 km

前后200米范围:
  开始点索引: 6082
  结束点索引: 7209
  开始时间: 2025-10-05T03:39:44Z
  结束时间: 2025-10-05T03:58:31Z
  前距离: 199.4 米
  后距离: 199.5 米
  数据点数: 1128
  时长: 0:18:47
  相对开始时间偏移: 1:41:25
  相对结束时间偏移: 2:00:12

这段的统计信息:
  海拔范围: 1906.0 - 1963.4 米
  海拔上升: 57.4 米
  心率范围: 76 - 139 BPM
  平均心率: 101 BPM

生成HUD的命令:
python3 gpx_hud_overlay.py hike.gpx -s 6082 -e 7209 -o summit_hud.mov
或者按时间:
python3 gpx_hud_overlay.py hike.gpx -st 01:41:25 -et 02:00:12 -o summit_hud.mov
```

**说明**：
- `find_summit.py` 自动找到 GPX 文件中的最高海拔点
- 计算该点前后各 200 米的范围
- 提供数据点索引和时间偏移
- 输出直接可用的生成命令

### 第 2 步：生成 HUD 视频

#### 方式 A：按时间段生成
```bash
# 生成从 2:30:00 到 2:40:00 的 HUD 视频
python3 gpx_hud_overlay.py hike.gpx -st 02:30:00 -et 02:40:00 -o my_hud.mov
```

#### 方式 B：按数据点索引生成
```bash
# 生成第 1000 到 3000 个数据点的视频
python3 gpx_hud_overlay.py hike.gpx -s 1000 -e 3000 -o my_hud.mov
```

#### 方式 C：生成完整视频
```bash
# 生成整个徒步的 HUD
python3 gpx_hud_overlay.py hike.gpx -o overlay_full.mov
```

### 第 3 步：在视频编辑软件中合成

#### Final Cut Pro
1. 导入主视频到时间线
2. 将 `my_hud.mov` 拖到上层轨道
3. 自动识别 Alpha 通道，下层视频显示在透明区域
4. 可调整位置和透明度
5. 导出成品

#### DaVinci Resolve
1. 导入主视频
2. 将 `my_hud.mov` 放在 Video 2 轨道上
3. 自动处理透明度
4. 调整缩放和位置
5. 导出

#### Adobe Premiere
1. 导入主视频和 HUD 视频
2. HUD 放在上方轨道
3. 混合模式为 Normal（自动支持 Alpha）
4. 调整大小和位置
5. 导出

---

## 📝 命令参数详解

```bash
python3 gpx_hud_overlay.py <gpx_file> [参数]
```

### 必需参数
- `gpx_file` - GPX 文件路径（例：`hike.gpx`）

### 可选参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `-o, --output` | 输出视频文件名 | `overlay.mov` |
| `-s, --start` | 开始数据点索引 | `0` |
| `-e, --end` | 结束数据点索引 | `5000` |
| `-st, --start-time` | 开始时间 (HH:MM:SS) | `02:30:00` |
| `-et, --end-time` | 结束时间 (HH:MM:SS) | `02:45:00` |
| `-w, --width` | 视频宽度像素 | `1920` |
| `--height` | 视频高度像素 | `1080` |
| `-f, --fps` | 帧率 | `30` |
| `--real-time` | 视频时长 = 实际徒步时长 | `--real-time` |
| `--no-map` | 隐藏路线地图 | `--no-map` |

### HUD 显示内容

生成的视频右下角显示 4 项实时徒步数据：
- **HR**: 心率（BPM，如果 GPX 有数据）
- **ALT**: 当前海拔（米）
- **DIST**: 累计距离（公里）
- **TIME**: 徒步经过的时间（HH:MM:SS）

---

## 🔍 实用示例
```bash
# 根据分析结果，从数据点 8000 到 10000
python3 gpx_hud_overlay.py hike.gpx -s 8000 -e 10000 -o summit_dash.mov
```

### 示例 2：生成 10 分钟精彩片段
```bash
# 从 3:00:00 到 3:10:00
python3 gpx_hud_overlay.py hike.gpx -st 03:00:00 -et 03:10:00 -o highlight.mov
```

### 示例 3：生成 720p 版本（节省空间）
```bash
python3 gpx_hud_overlay.py hike.gpx -w 1280 --height 720 -o overlay_720p.mov
```

### 示例 4：生成 24fps 电影质感版本
```bash
python3 gpx_hud_overlay.py hike.gpx -f 24 -o overlay_24fps.mov
```

### 示例 5：只要前 30 分钟
```bash
# 前 30 分钟 ≈ 1800 个数据点（按每秒 1 个数据点）
python3 gpx_hud_overlay.py hike.gpx -e 1800 -o first_30min.mov
```

### 示例 6：生成实时时长视频
```bash
# 视频时长 = 实际徒步时长（4 小时 9 分）
python3 gpx_hud_overlay.py hike.gpx --real-time -o full_realtime.mov
```

### 示例 7：特定时间段的实时视频
```bash
# 生成 2:00 到 3:00 的 1 小时视频
python3 gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 03:00:00 --real-time -o hour_segment.mov
```

### 示例 8：生成最高海拔点周边视频 ⛰️
```bash
# 生成最高海拔点（1963.4m）前后各 200 米的片段
# 数据点索引方式（更精确）
python3 gpx_hud_overlay.py hike.gpx -s 6082 -e 7209 -o summit_hud.mov

# 或者用时间偏移方式（01:41:25 到 02:00:12）
python3 gpx_hud_overlay.py hike.gpx -st 01:41:25 -et 02:00:12 -o summit_hud.mov

# 结合实时时长模式，生成 18 分 47 秒的视频
python3 gpx_hud_overlay.py hike.gpx -s 6082 -e 7209 --real-time -o summit_hud_realtime.mov
```

**登顶片段统计**：
- **最高海拔**: 1963.4 米
- **片段范围**: 前 199.4m + 后 199.5m
- **数据点数**: 1,128 个
- **时间长度**: 18 分 47 秒
- **海拔变化**: 1906.0m ~ 1963.4m（上升 57.4m）
- **平均心率**: 101 BPM（范围 76-139）

---

## ⚡ 实时时长模式

使用 `--real-time` 参数使生成的视频时长等于实际的徒步时长。

```bash
python3 gpx_hud_overlay.py hike.gpx --real-time -o overlay_realtime.mov
```

**工作原理**：
- 脚本自动计算选中数据点的实际时间差
- 根据数据点数和时间差计算适当的 fps
- 最终视频时长 = 实际徒步时长

**示例计算**：
- 500 个数据点，实际时长 500 秒 → fps = 1.0 → 视频 8 分 20 秒
- 14,164 个数据点，实际时长 ~15,000 秒 → fps ≈ 0.94 → 视频 4 小时 9 分

---

## ⚡ 性能优化

如果生成速度太慢：

### 1. 降低分辨率
```bash
python3 gpx_hud_overlay.py hike.gpx -w 960 --height 540 -o fast.mov
```

### 2. 只生成需要的部分
```bash
# 只生成 500 个数据点（~8 分钟）
python3 gpx_hud_overlay.py hike.gpx -s 0 -e 500 -o segment.mov
```

### 3. 隐藏地图（加快生成）
```bash
# 只显示数据面板，不绘制地图
python3 gpx_hud_overlay.py hike.gpx --no-map -o fast_no_map.mov
```

### 组合优化
```bash
# 720p + 24fps + 隐藏地图 + 只要中间 1 小时
python3 gpx_hud_overlay.py hike.gpx -s 3600 -e 7200 -w 1280 --height 720 -f 24 --no-map -o optimize.mov
```

### 3. 降低帧率
```bash
# 24fps 而不是 30fps
python3 gpx_hud_overlay.py hike.gpx -f 24 -o output.mov
```

### 4. 组合优化
```bash
# 720p + 24fps + 只要中间 1 小时
python3 gpx_hud_overlay.py hike.gpx -s 3600 -e 7200 -w 1280 --height 720 -f 24 -o optimize.mov
```

---

## 🎨 自定义 HUD 样式

编辑 `gpx_hud_overlay.py` 中的 `HUDOverlayGenerator` 类：

### 改变颜色
```python
self.font_color = (255, 255, 255)  # RGB: 白色
self.bg_color = (0, 0, 0)          # RGB: 黑色
```

### 改变透明度
```python
self.alpha = 0.7  # 0.0 完全透明，1.0 完全不透明
```

### 改变位置
编辑 `create_frame()` 方法中的坐标值

---

## 📊 数据统计

从 `analyze_gpx.py` 的结果可知：

- **总数据点数**: 14,164
- **总时长**: 4 小时 9 分
- **海拔范围**: 1,176.8m - 1,963.4m
- **平均海拔**: 1,597.9m
- **心率数据**: 无（此 GPX 未记录）

时间参考（每 2 分钟一个数据点）：
- 02:00:00 → 数据点 120
- 03:00:00 → 数据点 3,720
- 04:00:00 → 数据点 7,320
- 05:00:00 → 数据点 10,920

---

## 🐛 常见问题

**Q: ffmpeg 找不到？**
```bash
# Mac
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg

# 或验证是否安装
which ffmpeg
ffmpeg -version
```

**Q: Python 依赖错误？**
```bash
pip3 install --upgrade opencv-python numpy
```

**Q: 为什么心率显示 None？**
此 GPX 文件没有记录心率数据，但脚本会继续显示海拔和距离

**Q: 文件太大了？**
- 降低分辨率：`-w 1280 --height 720`
- 降低帧率：`-f 15`
- 只生成部分：`-s 0 -e 500`

**Q: 如何改变 HUD 背景颜色？**
编辑 `gpx_hud_overlay.py`：
```python
self.bg_color = (0, 255, 0)  # 改成绿色
```

---

## 📌 重要提示

1. **Alpha 通道支持** - 输出格式为 QuickTime RLE，支持透明通道，所有主流视频编辑软件都能识别

2. **数据点频率** - 每个数据点对应约 1 秒，所以 60 个数据点 ≈ 1 分钟视频

3. **坐标计算** - 使用 Haversine 公式计算球面距离，精度较高

4. **时间同步** - HUD 时间显示的是徒步经过的时间，不是绝对时间

---

## 📚 相关资源

- [FFmpeg 官网](https://ffmpeg.org/)
- [OpenCV 文档](https://docs.opencv.org/)
- [GPX 格式规范](https://www.topografix.com/gpx.asp)

---

**版本**: 1.0  
**最后更新**: 2025-12-21  
**作者**: GPX HUD Overlay Generator
