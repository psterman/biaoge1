from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # 创建一个512x512的图像，使用纯色背景
    size = 512
    image = Image.new('RGB', (size, size), '#4CAF50')  # 使用绿色背景
    draw = ImageDraw.Draw(image)
    
    try:
        # 尝试加载微软雅黑字体
        font_size = int(size * 0.8)  # 使用更大的字体
        font = ImageFont.truetype("msyh.ttc", font_size, encoding="unic")
    except:
        # 如果找不到，使用默认字体
        font = ImageFont.load_default()
    
    # 绘制"哥"字
    text = "哥"
    # 获取文字边界框
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 计算居中位置
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    
    # 绘制白色文字
    draw.text((text_x, text_y), text, fill='white', font=font)
    
    # 保存ICO文件
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    icons = []
    for s in icon_sizes:
        icons.append(image.resize(s, Image.Resampling.LANCZOS))
    
    icons[0].save("icon.ico", format='ICO', sizes=icon_sizes)
    print("图标文件已生成完成！")

if __name__ == "__main__":
    create_icon() 