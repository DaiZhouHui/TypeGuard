"""
创建默认图标文件
"""

import os
from PIL import Image, ImageDraw

def create_default_icon():
    """创建默认图标"""
    # 创建config目录
    if not os.path.exists("config"):
        os.makedirs("config")
    
    # 创建一个简单的触控板图标
    img = Image.new('RGBA', (256, 256), (70, 130, 180, 255))  # 钢蓝色背景
    draw = ImageDraw.Draw(img)
    
    # 绘制触控板形状（矩形）
    draw.rectangle([50, 50, 206, 206], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=4)
    
    # 绘制触控板指示器
    draw.ellipse([120, 120, 136, 136], fill=(0, 120, 215, 255))  # 蓝色圆点
    
    # 绘制键盘按键
    draw.rectangle([80, 170, 176, 190], fill=(200, 200, 200, 255), outline=(100, 100, 100, 255), width=2)
    draw.text((85, 173), "F11", fill=(0, 0, 0, 255))
    
    # 保存为ICO文件
    icon_path = os.path.join("config", "icon.ico")
    
    # 需要不同尺寸的图标
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(icon_path, format='ICO', sizes=sizes)
    
    print(f"已创建默认图标: {icon_path}")
    print("建议: 您可以替换此图标为自定义图标")
    
    return icon_path

if __name__ == "__main__":
    create_default_icon()