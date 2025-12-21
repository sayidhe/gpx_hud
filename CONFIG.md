# GPX HUD Overlay 配置和使用指南

## 功能说明
将 GPX 徒步数据（心率、海拔、距离）生成带透明通道的 HUD 叠加视频，可直接叠加在 vlog 视频上。

## 依赖安装

```bash
# 安装 Python 依赖
pip install opencv-python numpy

# 安装 ffmpeg（Mac）
brew install ffmpeg

# 或者在其他系统上
# Windows: choco install ffmpeg
# Linux: sudo apt-get install ffmpeg
```

## 基本用法

### 1. 生成完整徒步视频
```bash
python gpx_hud_overlay.py hike.gpx -o overlay.mov
```

### 2. 生成特定时间段的视频（按索引）
```bash
# 从第 1000 个点到第 5000 个点
python gpx_hud_overlay.py hike.gpx -o overlay_segment.mov -s 1000 -e 5000
```

### 3. 生成特定时间段的视频（按时间）
```bash
# 从 02:30:00 到 02:45:00
python gpx_hud_overlay.py hike.gpx -o overlay_segment.mov -st 02:30:00 -et 02:45:00
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `gpx_file` | GPX 文件路径 | `hike.gpx` |
| `-o, --output` | 输出视频文件名 | `overlay.mov` |
| `-s, --start` | 开始数据点索引 | `0` |
| `-e, --end` | 结束数据点索引 | `5000` |
| `-st, --start-time` | 开始时间 | `02:30:00` |
| `-et, --end-time` | 结束时间 | `02:45:00` |
| `-w, --width` | 视频宽度像素 | `1920` |
| `--height` | 视频高度像素 | `1080` |
| `-f, --fps` | 帧率 | `30` |
| `--real-time` | 生成视频时长与实际徒步时长相同 | `--real-time` |
| `--no-map` | 隐藏路线地图 | `--no-map` |

## 输出视频说明

### 视频格式
- **编码**: QuickTime RLE (qtrle) with Alpha
- **分辨率**: 1920×1080（可自定义）
- **帧率**: 30fps（可自定义）
- **Alpha 通道**: 支持透明背景，可直接叠加到其他视频上

### HUD 信息显示
输出视频右下角显示以下实时数据：
- **HR**: 心率（BPM）
- **ALT**: 海拔高度（米）
- **DIST**: 累计距离（公里）
- **TIME**: 运动时间

## 在视频编辑中使用

### DaVinci Resolve
1. 导入主视频
2. 将 `overlay.mov` 作为上层轨道导入
3. 使用透明度混合模式即可看到透明背景

### Final Cut Pro
1. 将 `overlay.mov` 拖到上层轨道
2. 自动识别 Alpha 通道，透明区域会显示下层内容

### Adobe Premiere
1. 在时间线中导入 `overlay.mov`
2. 确保上层轨道的混合模式为 Normal（已支持 Alpha）

## 性能优化

如果生成视频较慢，可以尝试：

1. **减少数据量**：只生成需要的时间段
```bash
python gpx_hud_overlay.py hike.gpx -st 02:00:00 -et 02:15:00 -o short.mov
```

2. **降低分辨率**：
```bash
python gpx_hud_overlay.py hike.gpx -w 1280 -h 720 -o overlay_720p.mov
```

3. **降低帧率**：
```bash
python gpx_hud_overlay.py hike.gpx -f 24 -o overlay_24fps.mov
```

4. **隐藏路线地图**（只显示数据，加快生成速度）：
```bash
python gpx_hud_overlay.py hike.gpx --no-map -o overlay_no_map.mov
```

## 常见问题

### Q: ffmpeg 找不到？
**A**: 需要先安装 ffmpeg
```bash
brew install ffmpeg  # macOS
```

### Q: 如何查看 GPX 文件有多少数据点？
**A**: 使用以下命令：
```python
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('hike.gpx')
root = tree.getroot()
ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
points = root.findall('.//gpx:trkpt', ns)
print(f'总数据点: {len(points)}')
"
```

### Q: 如何自定义 HUD 样式？
**A**: 编辑 `gpx_hud_overlay.py` 中的 `HUDOverlayGenerator` 类：
- `font_color`: 修改字体颜色
- `bg_color`: 修改背景颜色
- `alpha`: 修改背景透明度（0-1）
- 修改 `create_frame()` 方法来改变布局

## 示例工作流

```bash
# 1. 查看数据
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('hike.gpx')
root = tree.getroot()
ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
points = root.findall('.//gpx:trkpt', ns)
first = points[0].find('gpx:time', ns).text
last = points[-1].find('gpx:time', ns).text
print(f'时间范围: {first} 到 {last}')
print(f'总数据点: {len(points)}')
"

# 2. 生成特定时间段的 HUD
python gpx_hud_overlay.py hike.gpx -st 02:30:00 -et 02:45:00 -o hud_segment.mov

# 3. 在视频编辑软件中将 hud_segment.mov 叠加到主视频上
```

## 技术细节

- **距离计算**: 使用 Haversine 公式计算球面距离
- **视频编码**: 使用 QuickTime RLE 保证 Alpha 通道兼容性
- **数据同步**: 每个数据点对应一帧视频（30fps 时，1 秒内有 30 个数据点）

## 许可和支持

这是一个开源工具，可自由修改和使用。
