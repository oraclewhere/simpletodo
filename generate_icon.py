#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成应用图标 (app.ico)
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("PIL not available, skipping icon generation")
    exit(1)

# 创建一个 256x256 的图像
size = 256
img = Image.new('RGBA', (size, size), color=(52, 152, 219, 255))  # 蓝色背景
draw = ImageDraw.Draw(img)

# 绘制中文字 "待" 作为图标中心
try:
    # 尝试使用 Windows 系统字体
    font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 120)
except:
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttf", 120)
    except:
        # 如果没有中文字体，用英文
        font = ImageFont.load_default()

# 在中心绘制文本
text = "待"
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (size - text_width) // 2
y = (size - text_height) // 2 - 10
draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

# 保存为 ICO 文件
ico_path = os.path.join(os.path.dirname(__file__), 'app.ico')
img.save(ico_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
print(f"Icon created: {ico_path}")
