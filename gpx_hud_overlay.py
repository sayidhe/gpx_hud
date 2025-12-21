#!/usr/bin/env python3
"""
GPX HUD Overlay Generator
将 GPX 徒步数据（心率、海拔、距离）生成带透明通道的 HUD 叠加视频
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import os
import sys
from typing import List, Tuple
import math

try:
    import cv2
    import numpy as np
except ImportError:
    print("需要安装依赖: pip install opencv-python numpy")
    sys.exit(1)


class GPXParser:
    """GPX 文件解析器"""
    
    def __init__(self, gpx_file: str):
        self.gpx_file = gpx_file
        self.tree = ET.parse(gpx_file)
        self.root = self.tree.getroot()
        self.namespace = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
        }
    
    def parse_trackpoints(self) -> List[dict]:
        """解析轨迹点"""
        trackpoints = []
        for trkpt in self.root.findall('.//gpx:trkpt', self.namespace):
            lat = float(trkpt.get('lat'))
            lon = float(trkpt.get('lon'))
            ele_elem = trkpt.find('gpx:ele', self.namespace)
            ele = float(ele_elem.text) if ele_elem is not None else 0
            
            time_elem = trkpt.find('gpx:time', self.namespace)
            time = time_elem.text if time_elem is not None else None
            
            hr = None
            hr_elem = trkpt.find('.//gpxtpx:hr', self.namespace)
            if hr_elem is not None:
                hr = int(hr_elem.text)
            
            trackpoints.append({
                'lat': lat,
                'lon': lon,
                'ele': ele,
                'time': time,
                'hr': hr
            })
        
        return trackpoints
    
    def calculate_distance(self, trackpoints: List[dict]) -> List[float]:
        """计算累计距离（米）"""
        distances = [0.0]
        
        for i in range(1, len(trackpoints)):
            prev = trackpoints[i-1]
            curr = trackpoints[i]
            
            # 使用 Haversine 公式计算球面距离
            lat1, lon1 = math.radians(prev['lat']), math.radians(prev['lon'])
            lat2, lon2 = math.radians(curr['lat']), math.radians(curr['lon'])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            r = 6371000  # 地球半径（米）
            
            distance = r * c
            distances.append(distances[-1] + distance)
        
        return distances


class HUDOverlayGenerator:
    """HUD 叠加视频生成器"""
    
    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30, show_map: bool = True):
        self.width = width
        self.height = height
        self.fps = fps
        self.show_map = show_map
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 1.0
        self.font_color = (255, 255, 255)  # 白色
        self.bg_color = (0, 0, 0)  # 黑色背景
        self.alpha = 0.7  # 背景透明度
        
        # HUD 布局参数（顶部）
        self.hud_height = 250  # HUD 高度
        self.hud_left_width = 400  # 左侧数据区宽度
        
        # 地图参数
        self.map_width = 350  # 地图宽度
        self.map_height = 250  # 地图高度
        self.map_padding = 20  # 地图内边距
    
    def calculate_map_bounds(self, trackpoints: List[dict]) -> Tuple[float, float, float, float]:
        """计算地图边界（min_lat, max_lat, min_lon, max_lon）"""
        lats = [p['lat'] for p in trackpoints]
        lons = [p['lon'] for p in trackpoints]
        return min(lats), max(lats), min(lons), max(lons)
    
    def latlon_to_xy(self, lat: float, lon: float, bounds: Tuple[float, float, float, float]) -> Tuple[int, int]:
        """将地理坐标转换为地图像素坐标"""
        min_lat, max_lat, min_lon, max_lon = bounds
        
        # 计算归一化坐标（0-1）
        norm_x = (lon - min_lon) / (max_lon - min_lon) if max_lon > min_lon else 0.5
        norm_y = (max_lat - lat) / (max_lat - min_lat) if max_lat > min_lat else 0.5
        
        # 转换为像素坐标（留出边距）
        x = int(self.map_padding + norm_x * (self.map_width - 2 * self.map_padding))
        y = int(self.map_padding + norm_y * (self.map_height - 2 * self.map_padding))
        
        return x, y
    
    def draw_map(self, frame: np.ndarray, trackpoints: List[dict], current_idx: int) -> np.ndarray:
        """在HUD右下角绘制地图"""
        if len(trackpoints) < 2:
            return frame
        
        # 创建地图画布
        map_canvas = np.zeros((self.map_height, self.map_width, 4), dtype=np.uint8)
        map_canvas[:, :] = [0, 0, 0, int(255 * self.alpha)]  # 与左侧数据区一致的半透明黑色背景
        
        # 计算地图边界
        bounds = self.calculate_map_bounds(trackpoints)
        
        # 绘制后续路线（灰色）
        for i in range(current_idx, len(trackpoints) - 1):
            x1, y1 = self.latlon_to_xy(trackpoints[i]['lat'], trackpoints[i]['lon'], bounds)
            x2, y2 = self.latlon_to_xy(trackpoints[i + 1]['lat'], trackpoints[i + 1]['lon'], bounds)
            cv2.line(map_canvas, (x1, y1), (x2, y2), (100, 100, 100, 255), 2)
        
        # 绘制已走路线（#ffea00 - 亮黄色）
        if current_idx > 0:
            for i in range(0, current_idx):
                if i + 1 < current_idx:
                    x1, y1 = self.latlon_to_xy(trackpoints[i]['lat'], trackpoints[i]['lon'], bounds)
                    x2, y2 = self.latlon_to_xy(trackpoints[i + 1]['lat'], trackpoints[i + 1]['lon'], bounds)
                    # RGB 格式: #ffea00 = (255, 234, 0)
                    cv2.line(map_canvas, (x1, y1), (x2, y2), (255, 234, 0, 255), 3)
        
        # 绘制当前位置（暗黄色圆点）
        if current_idx < len(trackpoints):
            x, y = self.latlon_to_xy(trackpoints[current_idx]['lat'], trackpoints[current_idx]['lon'], bounds)
            cv2.circle(map_canvas, (x, y), 6, (204, 170, 0, 255), -1)
        
        # 绘制起点（暗黄色）
        if trackpoints:
            x, y = self.latlon_to_xy(trackpoints[0]['lat'], trackpoints[0]['lon'], bounds)
            cv2.circle(map_canvas, (x, y), 4, (204, 170, 0, 255), -1)
        
        # 不绘制边框，保持透明效果
        
        # 将地图贴到主帧顶部右侧（使用统一的 20px 边距）
        margin = 20
        y_offset = margin
        x_offset = self.width - self.map_width - margin
        
        # 使用 Alpha 混合
        map_alpha = map_canvas[:, :, 3:4] / 255.0
        frame[y_offset:y_offset + self.map_height, x_offset:x_offset + self.map_width, :3] = \
            (1 - map_alpha) * frame[y_offset:y_offset + self.map_height, x_offset:x_offset + self.map_width, :3] + \
            map_alpha * map_canvas[:, :, :3]
        # 只在地图有内容的地方更新alpha通道
        frame[y_offset:y_offset + self.map_height, x_offset:x_offset + self.map_width, 3] = \
            np.maximum(frame[y_offset:y_offset + self.map_height, x_offset:x_offset + self.map_width, 3],
                      map_canvas[:, :, 3])
        
        return frame
    
    def create_frame(self, time: str, hr: int, elevation: float, distance: float, 
                    trackpoints: List[dict] = None, current_idx: int = 0) -> np.ndarray:
        """创建单帧 HUD"""
        # 创建 RGBA 图像
        frame = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # 统一的边距设置
        bg_margin = 20  # 数据区块与视频边界的距离
        text_margin = 40  # 数据文字与视频边界的距离
        text_padding = 15  # 文字与背景之间的距离 = 15px（左右和底部边距）
        
        # 计算背景框的大小（紧凑围绕文字内容）
        line_height = 50
        data_bg_height = text_padding * 2 + line_height * 4  # 4 行文字 + 上下padding
        data_bg_width = 360  # 根据文字宽度调整
        
        # 顶部 HUD 区域背景（左上角，与视频边界距离为 bg_margin）
        frame[bg_margin:bg_margin + data_bg_height, bg_margin:bg_margin + data_bg_width] = [0, 0, 0, int(255 * self.alpha)]
        
        # 左侧数据显示（竖排列，与视频边界距离为 text_margin）
        # cv2.putText 的 y 坐标是基线位置，需要调整以使文字顶部对齐到 text_margin
        y_offset = text_margin + 25  # 增加 25px 以补偿文字基线
        x_offset = text_margin
        
        # 时间
        cv2.putText(frame, f"TIME: {time}", (x_offset, y_offset), 
                   self.font, self.font_scale, self.font_color + (255,), 2)
        
        # 心率
        if hr is not None:
            hr_text = f"HR: {hr} BPM"
            cv2.putText(frame, hr_text, (x_offset, y_offset + line_height), 
                       self.font, self.font_scale, self.font_color + (255,), 2)
        
        # 海拔
        ele_text = f"ALT: {elevation:.0f}m"
        cv2.putText(frame, ele_text, (x_offset, y_offset + line_height * 2),
                   self.font, self.font_scale, self.font_color + (255,), 2)
        
        # 距离
        dist_km = distance / 1000
        dist_text = f"DIST: {dist_km:.2f} km"
        cv2.putText(frame, dist_text, (x_offset, y_offset + line_height * 3),
                   self.font, self.font_scale, self.font_color + (255,), 2)
        
        # 绘制地图（如果启用）
        if trackpoints and self.show_map:
            frame = self.draw_map(frame, trackpoints, current_idx)
        
        return frame
    
    def generate_video(self, trackpoints: List[dict], distances: List[float],
                      start_idx: int = 0, end_idx: int = None,
                      output_file: str = "overlay.mov") -> bool:
        """生成 HUD 叠加视频"""
        
        if end_idx is None:
            end_idx = len(trackpoints)
        
        selected_points = trackpoints[start_idx:end_idx]
        selected_distances = distances[start_idx:end_idx]
        
        if not selected_points:
            print("错误：选中的时间段没有数据")
            return False
        
        print(f"处理 {len(selected_points)} 个数据点...")
        print(f"时间范围: {selected_points[0]['time']} 到 {selected_points[-1]['time']}")
        
        # 使用 ffmpeg 生成视频
        # 准备管道命令
        cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'rgba',
            '-s', f'{self.width}x{self.height}',
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'qtrle',  # QuickTime RLE with alpha
            '-y',
            output_file
        ]
        
        try:
            process = subprocess.Popen(cmd, stdin=subprocess.PIPE, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE)
            
            for i, point in enumerate(selected_points):
                # 将 UTC 时间转换为 UTC+8 时区
                if point['time']:
                    utc_time = datetime.fromisoformat(point['time'].replace('Z', '+00:00'))
                    cst_time = utc_time.astimezone(timezone(timedelta(hours=8)))
                    time_str = cst_time.strftime('%H:%M:%S')
                else:
                    time_str = "00:00:00"
                
                frame = self.create_frame(
                    time=time_str,
                    hr=point['hr'],
                    elevation=point['ele'],
                    distance=selected_distances[i],
                    trackpoints=selected_points,
                    current_idx=i
                )
                
                # 转换为字节数据发送给 ffmpeg
                process.stdin.write(frame.tobytes())
                
                if (i + 1) % 30 == 0:
                    print(f"  处理进度: {i + 1}/{len(selected_points)}")
            
            process.stdin.close()
            process.wait()
            
            if process.returncode == 0:
                print(f"✓ 成功生成视频: {output_file}")
                return True
            else:
                stderr = process.stderr.read().decode()
                print(f"✗ FFmpeg 错误: {stderr}")
                return False
        
        except FileNotFoundError:
            print("错误：未找到 ffmpeg，请先安装: brew install ffmpeg")
            return False
        except Exception as e:
            print(f"错误: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GPX HUD 叠加视频生成器')
    parser.add_argument('gpx_file', help='GPX 文件路径')
    parser.add_argument('-o', '--output', default='overlay.mov', help='输出视频文件')
    parser.add_argument('-s', '--start', type=int, default=0, help='开始数据点索引')
    parser.add_argument('-e', '--end', type=int, help='结束数据点索引')
    parser.add_argument('-st', '--start-time', help='开始时间 (HH:MM:SS)')
    parser.add_argument('-et', '--end-time', help='结束时间 (HH:MM:SS)')
    parser.add_argument('-w', '--width', type=int, default=1920, help='视频宽度')
    parser.add_argument('--height', type=int, default=1080, help='视频高度')
    parser.add_argument('-f', '--fps', type=int, default=30, help='帧率')
    parser.add_argument('--real-time', action='store_true', help='生成视频时长与实际徒步时长相同')
    parser.add_argument('--no-map', action='store_false', dest='show_map', help='隐藏路线地图')
    
    args = parser.parse_args()
    
    # 解析 GPX 文件
    print(f"正在读取 GPX 文件: {args.gpx_file}")
    parser_gpx = GPXParser(args.gpx_file)
    trackpoints = parser_gpx.parse_trackpoints()
    distances = parser_gpx.calculate_distance(trackpoints)
    
    print(f"总数据点数: {len(trackpoints)}")
    
    # 确定时间范围
    start_idx = args.start
    end_idx = args.end or len(trackpoints)
    
    if args.start_time or args.end_time:
        # 根据时间搜索索引
        for i, point in enumerate(trackpoints):
            if point['time']:
                pt_time = point['time'].split('T')[1].split('Z')[0]
                
                if args.start_time and pt_time >= args.start_time:
                    start_idx = i
                    args.start_time = None  # 标记为已找到，避免重复覆盖
                
                if args.end_time and pt_time >= args.end_time:
                    end_idx = i
                    break
    
    # 如果启用实时时长模式，自动计算 fps
    if args.real_time:
        selected_points = trackpoints[start_idx:end_idx]
        if selected_points and selected_points[0]['time'] and selected_points[-1]['time']:
            from datetime import datetime
            start_time_str = selected_points[0]['time']
            end_time_str = selected_points[-1]['time']
            
            start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            duration_seconds = (end_dt - start_dt).total_seconds()
            
            if duration_seconds > 0:
                # 计算需要的 fps 以匹配实际时长
                args.fps = len(selected_points) / duration_seconds
                print(f"实时模式: 自动计算 fps = {args.fps:.2f}（视频时长将为 {duration_seconds/3600:.1f} 小时）")
    
    # 生成视频
    generator = HUDOverlayGenerator(width=args.width, height=args.height, fps=args.fps, show_map=args.show_map)
    success = generator.generate_video(trackpoints, distances, start_idx, end_idx, args.output)
    
    if success:
        file_size = os.path.getsize(args.output) / (1024 * 1024)
        print(f"文件大小: {file_size:.1f} MB")
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
