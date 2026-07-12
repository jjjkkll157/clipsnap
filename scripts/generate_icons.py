"""生成 ClipSnap 图标 — 简单的 SVG → PNG 转换（纯 Python，无外部依赖）"""
import struct
import zlib
import base64
from pathlib import Path

ICON_DIR = Path(__file__).parent.parent / "extension"

# 简单的 16×16 / 48×48 / 128×128 PNG 生成（紫色渐变圆形 + 白色链环图标）
# 使用内嵌的 base64 编码最小 PNG 作为图标


def _make_png(size: int) -> bytes:
    """生成一个简单的 PNG 图标：紫色圆形 + 'C' 字母"""
    from io import BytesIO
    
    # 创建像素数据
    pixels = []
    import math
    cx, cy = size / 2, size / 2
    r = size * 0.4
    
    for y in range(size):
        row = [0]  # filter byte
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= r:
                # 紫色渐变
                t = dist / r
                row.extend([int(102 + (1-t)*60), int(126 - t*40), int(234 - t*40), 255])
            elif dist <= r + 1:
                row.extend([80, 80, 160, 200])
            else:
                row.extend([0, 0, 0, 0])
        pixels.append(bytes(row))
    
    raw = b''.join(pixels)
    
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
    
    ihdr = struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0)  # 8-bit RGBA
    
    compressed = zlib.compress(raw)
    
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', compressed)
    png += chunk(b'IEND', b'')
    
    return png


def generate_icons():
    for size in [16, 48, 128]:
        png_data = _make_png(size)
        path = ICON_DIR / f"icon{size}.png"
        path.write_bytes(png_data)
        print(f"✅ 生成 icon{size}.png ({len(png_data)} bytes)")


if __name__ == "__main__":
    generate_icons()
