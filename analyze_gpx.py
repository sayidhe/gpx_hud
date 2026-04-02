#!/usr/bin/env python3
"""
GPX 数据分析工具 - 帮助选择最佳时间段
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import sys


LOCAL_TIMEZONE = timezone(timedelta(hours=8))


def parse_gpx_time(time_str: str) -> datetime:
    """解析 GPX 的 UTC 时间字符串"""
    return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

def analyze_gpx(gpx_file: str):
    """分析 GPX 文件并显示统计信息"""
    
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    points = root.findall('.//gpx:trkpt', ns)
    
    print(f"\n{'='*60}")
    print(f"GPX 文件分析: {gpx_file}")
    print(f"{'='*60}\n")
    
    # 基本信息
    print(f"总数据点数: {len(points)}")
    
    if not points:
        print("没有找到数据点")
        return
    
    # 时间信息
    first_time_elem = points[0].find('gpx:time', ns)
    last_time_elem = points[-1].find('gpx:time', ns)
    example_start_time = "10:00:00"
    example_end_time = "10:15:00"
    
    if first_time_elem is not None and last_time_elem is not None:
        first_time = first_time_elem.text
        last_time = last_time_elem.text
        
        # 解析时间
        first_dt_utc = parse_gpx_time(first_time)
        last_dt_utc = parse_gpx_time(last_time)
        first_dt_local = first_dt_utc.astimezone(LOCAL_TIMEZONE)
        last_dt_local = last_dt_utc.astimezone(LOCAL_TIMEZONE)
        print(f"开始时间(UTC+8): {first_dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"结束时间(UTC+8): {last_dt_local.strftime('%Y-%m-%d %H:%M:%S')}")

        # 生成东八区示例时间（用于命令行建议）
        example_start_time = first_dt_local.replace(second=0).strftime('%H:%M:%S')
        example_end_time = (first_dt_local + timedelta(minutes=15)).replace(second=0).strftime('%H:%M:%S')

        duration = last_dt_utc - first_dt_utc
        print(f"总时长: {duration}")
    
    # 海拔信息
    elevations = []
    for point in points:
        ele_elem = point.find('gpx:ele', ns)
        if ele_elem is not None:
            elevations.append(float(ele_elem.text))
    
    if elevations:
        print(f"\n海拔统计:")
        print(f"  最低: {min(elevations):.1f}m")
        print(f"  最高: {max(elevations):.1f}m")
        print(f"  平均: {sum(elevations)/len(elevations):.1f}m")
    
    # 心率信息
    namespace = {'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}
    heart_rates = []
    for point in points:
        hr_elem = point.find('.//gpxtpx:hr', namespace)
        if hr_elem is not None:
            heart_rates.append(int(hr_elem.text))
    
    if heart_rates:
        print(f"\n心率统计:")
        print(f"  最低: {min(heart_rates)} BPM")
        print(f"  最高: {max(heart_rates)} BPM")
        print(f"  平均: {sum(heart_rates)/len(heart_rates):.0f} BPM")
    else:
        print(f"\n⚠️  未检测到心率数据")
    
    # 显示时间范围示例
    print(f"\n{'='*60}")
    print("时间范围示例（UTC+8，每 2 分钟）:")
    print(f"{'='*60}\n")
    
    for i, point in enumerate(points):
        time_elem = point.find('gpx:time', ns)
        if time_elem is not None:
            time_str = time_elem.text
            time_dt_local = parse_gpx_time(time_str).astimezone(LOCAL_TIMEZONE)
            time_only = time_dt_local.strftime('%H:%M:%S')
            
            if i % 120 == 0:  # 每 2 分钟
                ele_elem = point.find('gpx:ele', ns)
                ele = float(ele_elem.text) if ele_elem is not None else 0
                print(f"数据点 {i:>6d}: {time_only}  海拔: {ele:7.1f}m  (索引: {i})")
    
    print(f"\n{'='*60}\n")
    
    # 使用建议
    print("使用建议:")
    print(f"1. 按时间段生成 HUD:")
    print(f"   python gpx_hud_overlay.py hike.gpx -st {example_start_time} -et {example_end_time} -o overlay.mov")
    print(f"   （-st/-et 按 UTC+8，与上方时间示例一致）")
    print(f"\n2. 按数据点索引生成 HUD:")
    print(f"   python gpx_hud_overlay.py hike.gpx -s 0 -e 500 -o overlay.mov")
    print(f"\n3. 生成完整 HUD:")
    print(f"   python gpx_hud_overlay.py hike.gpx -o overlay_full.mov")
    print()

if __name__ == '__main__':
    gpx_file = 'hike.gpx'
    if len(sys.argv) > 1:
        gpx_file = sys.argv[1]
    
    analyze_gpx(gpx_file)
