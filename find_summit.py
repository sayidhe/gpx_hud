#!/usr/bin/env python3
"""
找到最高海拔点及其前后200米的范围
"""

import xml.etree.ElementTree as ET
from datetime import datetime
import math

# 解析 GPX 文件
tree = ET.parse('hike.gpx')
root = tree.getroot()
ns = {'gpx': 'http://www.topografix.com/GPX/1/1',
      'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'}

# 获取所有轨迹点
trackpoints = []
for trkpt in root.findall('.//gpx:trkpt', ns):
    lat = float(trkpt.get('lat'))
    lon = float(trkpt.get('lon'))
    ele_elem = trkpt.find('gpx:ele', ns)
    ele = float(ele_elem.text) if ele_elem is not None else 0
    
    time_elem = trkpt.find('gpx:time', ns)
    time = time_elem.text if time_elem is not None else None
    
    hr = None
    hr_elem = trkpt.find('.//gpxtpx:hr', ns)
    if hr_elem is not None:
        hr = int(hr_elem.text)
    
    trackpoints.append({
        'lat': lat,
        'lon': lon,
        'ele': ele,
        'time': time,
        'hr': hr,
        'index': len(trackpoints)
    })

print(f"总数据点数: {len(trackpoints)}")

# 计算累计距离
def haversine_distance(lat1, lon1, lat2, lon2):
    lat1, lon1 = math.radians(lat1), math.radians(lon1)
    lat2, lon2 = math.radians(lat2), math.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return 6371000 * c  # 地球半径米

distances = [0.0]
for i in range(1, len(trackpoints)):
    prev = trackpoints[i-1]
    curr = trackpoints[i]
    dist = haversine_distance(prev['lat'], prev['lon'], curr['lat'], curr['lon'])
    distances.append(distances[-1] + dist)

# 找到最高海拔点
max_ele_idx = 0
max_ele = trackpoints[0]['ele']
for i, tp in enumerate(trackpoints):
    if tp['ele'] > max_ele:
        max_ele = tp['ele']
        max_ele_idx = i

print(f"\n最高海拔点:")
print(f"  海拔: {max_ele:.1f} 米")
print(f"  数据点索引: {max_ele_idx}")
print(f"  时间: {trackpoints[max_ele_idx]['time']}")
print(f"  累计距离: {distances[max_ele_idx]/1000:.2f} km")

# 找前后200米的范围
target_distance = 200  # 前后各200米

# 向前找
start_idx = max_ele_idx
for i in range(max_ele_idx, -1, -1):
    if distances[max_ele_idx] - distances[i] <= target_distance:
        start_idx = i
    else:
        break

# 向后找
end_idx = max_ele_idx
for i in range(max_ele_idx, len(trackpoints)):
    if distances[i] - distances[max_ele_idx] <= target_distance:
        end_idx = i
    else:
        break

print(f"\n前后200米范围:")
print(f"  开始点索引: {start_idx}")
print(f"  结束点索引: {end_idx}")
print(f"  开始时间: {trackpoints[start_idx]['time']}")
print(f"  结束时间: {trackpoints[end_idx]['time']}")
print(f"  前距离: {distances[max_ele_idx] - distances[start_idx]:.1f} 米")
print(f"  后距离: {distances[end_idx] - distances[max_ele_idx]:.1f} 米")
print(f"  数据点数: {end_idx - start_idx + 1}")

# 计算这段时间的时长
start_time = datetime.fromisoformat(trackpoints[start_idx]['time'].replace('Z', '+00:00'))
end_time = datetime.fromisoformat(trackpoints[end_idx]['time'].replace('Z', '+00:00'))
duration = end_time - start_time
print(f"  时长: {duration}")

# 计算从开始到这段的偏移时间
first_time = datetime.fromisoformat(trackpoints[0]['time'].replace('Z', '+00:00'))
start_offset = start_time - first_time
end_offset = end_time - first_time
print(f"  相对开始时间偏移: {start_offset}")
print(f"  相对结束时间偏移: {end_offset}")

# 统计这段的海拔、心率
segment_eles = [tp['ele'] for tp in trackpoints[start_idx:end_idx+1]]
segment_hrs = [tp['hr'] for tp in trackpoints[start_idx:end_idx+1] if tp['hr'] is not None]

print(f"\n这段的统计信息:")
print(f"  海拔范围: {min(segment_eles):.1f} - {max(segment_eles):.1f} 米")
print(f"  海拔上升: {max(segment_eles) - min(segment_eles):.1f} 米")
if segment_hrs:
    print(f"  心率范围: {min(segment_hrs)} - {max(segment_hrs)} BPM")
    print(f"  平均心率: {sum(segment_hrs)/len(segment_hrs):.0f} BPM")

# 输出生成命令
hours, remainder = divmod(int(start_offset.total_seconds()), 3600)
minutes, seconds = divmod(remainder, 60)
print(f"\n生成HUD的命令:")
print(f"python3 gpx_hud_overlay.py hike.gpx -s {start_idx} -e {end_idx} -o summit_hud.mov")
print(f"或者按时间:")
print(f"python3 gpx_hud_overlay.py hike.gpx -st {hours:02d}:{minutes:02d}:{seconds:02d} -et ", end="")
hours2, remainder = divmod(int(end_offset.total_seconds()), 3600)
minutes2, seconds2 = divmod(remainder, 60)
print(f"{hours2:02d}:{minutes2:02d}:{seconds2:02d} -o summit_hud.mov")
