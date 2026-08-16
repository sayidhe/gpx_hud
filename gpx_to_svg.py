#!/usr/bin/env python3
"""
GPX 轨迹转 SVG 工具 - 按海拔/速度/心率/进度给路线上色

示例:
    python gpx_to_svg.py "route_2026-07-20_5.45pm.gpx" -o route.svg
    python gpx_to_svg.py "route_2026-07-20_5.45pm.gpx" -o route.svg --color-by speed
"""

import argparse
import math
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

GPX_NS = 'http://www.topografix.com/GPX/1/1'
GPXTPX_NS = 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
NS = {'gpx': GPX_NS, 'gpxtpx': GPXTPX_NS}

# 绿-黄-红配色表的锚点 (t, (r, g, b))
COLOR_STOPS = [
    (0.00, (34, 197, 94)),
    (0.50, (250, 204, 21)),
    (1.00, (220, 38, 38)),
]


def colormap(t: float) -> str:
    """将 [0, 1] 的比例值映射到十六进制颜色"""
    t = min(1.0, max(0.0, t))
    for (t0, c0), (t1, c1) in zip(COLOR_STOPS, COLOR_STOPS[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            r = round(c0[0] + (c1[0] - c0[0]) * f)
            g = round(c0[1] + (c1[1] - c0[1]) * f)
            b = round(c0[2] + (c1[2] - c0[2]) * f)
            return f'#{r:02x}{g:02x}{b:02x}'
    return f'#{COLOR_STOPS[-1][1][0]:02x}{COLOR_STOPS[-1][1][1]:02x}{COLOR_STOPS[-1][1][2]:02x}'


def parse_trackpoints(gpx_file: str):
    tree = ET.parse(gpx_file)
    root = tree.getroot()
    points = []
    for pt in root.findall('.//gpx:trkpt', NS):
        lat = float(pt.get('lat'))
        lon = float(pt.get('lon'))

        ele_elem = pt.find('gpx:ele', NS)
        ele = float(ele_elem.text) if ele_elem is not None else None

        speed_elem = pt.find('gpx:extensions/gpx:speed', NS)
        speed = float(speed_elem.text) if speed_elem is not None else None

        hr_elem = pt.find('.//gpxtpx:hr', NS)
        hr = float(hr_elem.text) if hr_elem is not None else None

        points.append({'lat': lat, 'lon': lon, 'ele': ele, 'speed': speed, 'hr': hr})

    if not points:
        raise ValueError(f'{gpx_file} 中没有找到 <trkpt> 数据点')
    return points


def smooth(values, window: int):
    if window <= 1:
        return values
    half = window // 2
    n = len(values)
    result = []
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        chunk = [v for v in values[lo:hi] if v is not None]
        result.append(sum(chunk) / len(chunk) if chunk else None)
    return result


def clipped_range(values, clip_percentile: float):
    clean = sorted(v for v in values if v is not None)
    if not clean:
        return 0.0, 1.0
    if clip_percentile <= 0:
        return clean[0], clean[-1]
    lo_idx = int(len(clean) * (clip_percentile / 100.0))
    hi_idx = int(len(clean) * (1 - clip_percentile / 100.0))
    hi_idx = min(hi_idx, len(clean) - 1)
    return clean[lo_idx], clean[hi_idx]


def project(points, width: float, height: float, padding: float):
    mean_lat_rad = math.radians(sum(p['lat'] for p in points) / len(points))
    xs = [p['lon'] * math.cos(mean_lat_rad) for p in points]
    ys = [p['lat'] for p in points]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1e-9)
    span_y = max(max_y - min_y, 1e-9)

    avail_w = width - 2 * padding
    avail_h = height - 2 * padding
    scale = min(avail_w / span_x, avail_h / span_y)

    drawn_w = span_x * scale
    drawn_h = span_y * scale
    offset_x = padding + (avail_w - drawn_w) / 2
    offset_y = padding + (avail_h - drawn_h) / 2

    coords = []
    for x, y in zip(xs, ys):
        svg_x = offset_x + (x - min_x) * scale
        svg_y = offset_y + (max_y - y) * scale  # 纬度越大越靠上,需翻转
        coords.append((svg_x, svg_y))
    return coords


def build_svg(points, coords, color_by: str, width: float, height: float,
              stroke_width: float, background: str, show_legend: bool,
              smooth_window: int, clip_percentile: float) -> str:
    if color_by == 'progress':
        raw_values = list(range(len(points)))
        unit = ''
        label = 'Progress'
    elif color_by == 'speed':
        raw_values = [p['speed'] for p in points]
        unit = 'km/h'
        label = 'Speed'
    elif color_by == 'hr':
        raw_values = [p['hr'] for p in points]
        unit = 'bpm'
        label = 'Heart rate'
    else:
        raw_values = [p['ele'] for p in points]
        unit = 'm'
        label = 'Elevation'

    values = smooth(raw_values, smooth_window)
    vmin, vmax = clipped_range(values, clip_percentile)
    vrange = max(vmax - vmin, 1e-9)

    def value_at(i):
        v = values[i]
        return vmin if v is None else v

    def norm(i):
        return (value_at(i) - vmin) / vrange

    segments = []
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        t = (norm(i) + norm(i + 1)) / 2
        color = colormap(t)
        segments.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" />'
        )

    legend = ''
    if show_legend:
        legend_w, legend_h = 200, 14
        legend_x = width - legend_w - 20
        legend_y = height - 40
        stops = ''.join(
            f'<stop offset="{t*100:.0f}%" stop-color="{colormap(t)}" />'
            for t in [i / 10 for i in range(11)]
        )
        display_max = vmax * 3.6 if color_by == 'speed' else vmax
        display_min = vmin * 3.6 if color_by == 'speed' else vmin
        legend = f'''
  <defs>
    <linearGradient id="legend-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
      {stops}
    </linearGradient>
  </defs>
  <rect x="{legend_x}" y="{legend_y}" width="{legend_w}" height="{legend_h}"
        fill="url(#legend-gradient)" stroke="#ffffff" stroke-width="1" />
  <text x="{legend_x}" y="{legend_y - 6}" font-family="sans-serif" font-size="12"
        fill="#e5e5e5">{label} ({unit})</text>
  <text x="{legend_x}" y="{legend_y + legend_h + 14}" font-family="sans-serif" font-size="11"
        fill="#e5e5e5">{display_min:.0f}</text>
  <text x="{legend_x + legend_w}" y="{legend_y + legend_h + 14}" font-family="sans-serif"
        font-size="11" fill="#e5e5e5" text-anchor="end">{display_max:.0f}</text>
'''

    marker_radius = stroke_width * 2.5
    start_x, start_y = coords[0]
    end_x, end_y = coords[-1]
    markers = (
        f'<circle cx="{start_x:.2f}" cy="{start_y:.2f}" r="{marker_radius}" '
        f'fill="#22c55e" stroke="#ffffff" stroke-width="{stroke_width * 0.4}" />'
        f'<circle cx="{end_x:.2f}" cy="{end_y:.2f}" r="{marker_radius}" '
        f'fill="#dc2626" stroke="#ffffff" stroke-width="{stroke_width * 0.4}" />'
    )

    background_rect = (
        '' if background == 'transparent' else
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{background}" />'
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
     viewBox="0 0 {width} {height}">
  {background_rect}
  {''.join(segments)}
  {markers}
  {legend}
</svg>
'''
    return svg


def find_chrome():
    for name in ('google-chrome', 'chromium', 'chromium-browser'):
        path = shutil.which(name)
        if path:
            return path
    mac_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    return mac_path if os.path.exists(mac_path) else None


def render_png(svg_path: str, png_path: str, width: float, height: float, transparent: bool):
    chrome = find_chrome()
    if not chrome:
        sys.exit('未找到 Chrome/Chromium, 无法导出 PNG (可安装后重试, 或用浏览器手动打开 SVG 另存为 PNG)')
    abs_svg = os.path.abspath(svg_path)
    abs_png = os.path.abspath(png_path)
    cmd = [chrome, '--headless', '--disable-gpu', f'--screenshot={abs_png}',
           f'--window-size={int(width)},{int(height)}']
    if transparent:
        cmd.append('--default-background-color=00000000')
    cmd.append(f'file://{abs_svg}')
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not os.path.exists(abs_png):
        sys.exit(f'PNG 导出失败:\n{result.stderr}')


def main():
    parser = argparse.ArgumentParser(description='将 GPX 路线渲染为带颜色的 SVG')
    parser.add_argument('gpx_file', nargs='?', default='route_2026-07-20_5.45pm.gpx',
                         help='输入 GPX 文件路径')
    parser.add_argument('-o', '--output', default=None, help='输出 SVG 文件路径')
    parser.add_argument('--color-by', choices=['elevation', 'speed', 'hr', 'progress'],
                         default='elevation', help='按什么指标给路线上色 (默认: elevation)')
    parser.add_argument('--width', type=float, default=1200, help='SVG 宽度 (默认: 1200)')
    parser.add_argument('--height', type=float, default=1200, help='SVG 高度 (默认: 1200)')
    parser.add_argument('--padding', type=float, default=40, help='边距 (默认: 40)')
    parser.add_argument('--stroke-width', type=float, default=4, help='线宽 (默认: 4)')
    parser.add_argument('--background', default='#111111',
                         help='背景色, 传 "transparent" 可生成透明背景 (默认: #111111)')
    parser.add_argument('--legend', action='store_true', help='绘制颜色图例 (默认不绘制)')
    parser.add_argument('--smooth-window', type=int, default=5,
                         help='颜色数值的滑动平均窗口, 0 为不平滑 (默认: 5)')
    parser.add_argument('--clip-percentile', type=float, default=2.0,
                         help='首尾各裁剪多少百分位以避免异常值影响配色 (默认: 2.0)')
    parser.add_argument('--png', action='store_true',
                         help='额外通过 headless Chrome 导出同名 PNG')
    args = parser.parse_args()

    output = args.output or (args.gpx_file.rsplit('.', 1)[0] + f'_{args.color_by}.svg')

    points = parse_trackpoints(args.gpx_file)

    if args.color_by == 'speed' and all(p['speed'] is None for p in points):
        sys.exit('该 GPX 文件不包含 speed 数据, 无法按速度上色')
    if args.color_by == 'hr' and all(p['hr'] is None for p in points):
        sys.exit('该 GPX 文件不包含心率数据, 无法按心率上色')

    coords = project(points, args.width, args.height, args.padding)
    svg = build_svg(
        points, coords, args.color_by, args.width, args.height,
        args.stroke_width, args.background, args.legend,
        args.smooth_window, args.clip_percentile,
    )

    with open(output, 'w', encoding='utf-8') as f:
        f.write(svg)

    print(f'已生成: {output}')
    print(f'数据点数: {len(points)}  上色依据: {args.color_by}')

    if args.png:
        png_output = output.rsplit('.', 1)[0] + '.png'
        render_png(output, png_output, args.width, args.height, args.background == 'transparent')
        print(f'已生成: {png_output}')


if __name__ == '__main__':
    main()
