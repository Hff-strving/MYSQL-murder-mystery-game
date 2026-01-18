#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剧本封面图片批处理工具
功能：统一格式、尺寸，并按 Script_ID 重命名
依赖：pip install pillow
"""

import os
import sys
from pathlib import Path
from PIL import Image

# ==================== 配置区 ====================
# 剧本ID与中文名映射（必须与数据库一致）
SCRIPT_MAPPING = {
    1001: "年轮",
    1002: "漓川怪谈簿",
    1003: "极夜",
    1004: "云使",
    1005: "告别诗",
    1006: "就像水消失在水中",
    1007: "搞钱",
    1008: "青楼",
    1009: "刀鞘",
    1010: "古董局中局",
    1011: "桃花源记",
    1012: "一点半"
}

# 目标尺寸（宽x高）
TARGET_WIDTH = 600
TARGET_HEIGHT = 800

# 输出质量
JPEG_QUALITY = 85

# 路径配置（相对于项目根目录）
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "images"
OUTPUT_DIR = PROJECT_ROOT / "frontend-vue" / "public" / "assets" / "images"

# ==================== 工具函数 ====================

def ensure_output_dir():
    """确保输出目录存在"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ 输出目录已准备: {OUTPUT_DIR}")


def find_source_image(script_name):
    """
    根据剧本名查找源图片文件（支持多种扩展名）
    返回：Path对象或None
    """
    extensions = ['.png', '.jpg', '.jpeg', '.webp', '.PNG', '.JPG', '.JPEG', '.WEBP']

    for ext in extensions:
        file_path = INPUT_DIR / f"{script_name}{ext}"
        if file_path.exists():
            return file_path

    return None


def resize_and_crop(image, target_width, target_height):
    """
    等比缩放并居中裁剪到目标尺寸

    Args:
        image: PIL Image对象
        target_width: 目标宽度
        target_height: 目标高度

    Returns:
        处理后的PIL Image对象
    """
    # 转换为RGB模式（去除透明通道，适配JPEG）
    if image.mode in ('RGBA', 'LA', 'P'):
        # 创建白色背景
        background = Image.new('RGB', image.size, (255, 255, 255))
        if image.mode == 'P':
            image = image.convert('RGBA')
        background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
        image = background
    elif image.mode != 'RGB':
        image = image.convert('RGB')

    # 计算缩放比例（保证至少一边填满目标尺寸）
    img_width, img_height = image.size
    scale_w = target_width / img_width
    scale_h = target_height / img_height
    scale = max(scale_w, scale_h)  # 取较大的缩放比例

    # 等比缩放
    new_width = int(img_width * scale)
    new_height = int(img_height * scale)
    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # 居中裁剪
    left = (new_width - target_width) // 2
    top = (new_height - target_height) // 2
    right = left + target_width
    bottom = top + target_height

    image = image.crop((left, top, right, bottom))

    return image


def process_single_image(script_id, script_name):
    """
    处理单张图片

    Args:
        script_id: 剧本ID
        script_name: 剧本中文名

    Returns:
        bool: 是否成功
    """
    # 查找源文件
    source_path = find_source_image(script_name)
    if not source_path:
        print(f"✗ [{script_id}] {script_name}: 未找到源图片")
        return False

    # 输出文件名
    output_filename = f"script_{script_id}.jpg"
    output_path = OUTPUT_DIR / output_filename

    try:
        # 打开图片
        with Image.open(source_path) as img:
            # 处理图片
            processed_img = resize_and_crop(img, TARGET_WIDTH, TARGET_HEIGHT)

            # 保存为JPEG（去除EXIF）
            processed_img.save(
                output_path,
                'JPEG',
                quality=JPEG_QUALITY,
                optimize=True,
                exif=b''  # 去除EXIF信息
            )

        print(f"✓ [{script_id}] {script_name}: {source_path.name} → {output_filename}")
        return True

    except Exception as e:
        print(f"✗ [{script_id}] {script_name}: 处理失败 - {str(e)}")
        return False


def create_default_image():
    """创建默认占位图"""
    output_path = OUTPUT_DIR / "default.jpg"

    try:
        # 创建纯色背景
        img = Image.new('RGB', (TARGET_WIDTH, TARGET_HEIGHT), color=(45, 45, 60))

        # 保存
        img.save(output_path, 'JPEG', quality=JPEG_QUALITY)
        print(f"✓ 默认图片已创建: default.jpg")
        return True

    except Exception as e:
        print(f"✗ 创建默认图片失败: {str(e)}")
        return False


# ==================== 主函数 ====================

def main():
    """主执行函数"""
    print("=" * 60)
    print("剧本封面图片批处理工具")
    print("=" * 60)
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"目标尺寸: {TARGET_WIDTH}x{TARGET_HEIGHT}")
    print(f"输出质量: {JPEG_QUALITY}")
    print("=" * 60)

    # 检查输入目录
    if not INPUT_DIR.exists():
        print(f"✗ 错误：输入目录不存在 - {INPUT_DIR}")
        print("请确保项目根目录下存在 images/ 文件夹（原始封面图）")
        sys.exit(1)

    # 确保输出目录存在
    ensure_output_dir()

    # 处理所有剧本封面
    print("\n开始处理剧本封面...")
    success_count = 0
    fail_count = 0

    for script_id, script_name in sorted(SCRIPT_MAPPING.items()):
        if process_single_image(script_id, script_name):
            success_count += 1
        else:
            fail_count += 1

    # 创建默认图片
    print("\n创建默认占位图...")
    create_default_image()

    # 输出统计
    print("\n" + "=" * 60)
    print(f"处理完成！成功: {success_count}, 失败: {fail_count}")
    print("=" * 60)

    if fail_count > 0:
        print("\n⚠️  部分图片处理失败，请检查上述错误信息")
        sys.exit(1)
    else:
        print("\n✅ 所有图片处理成功！")
        print(f"输出位置: {OUTPUT_DIR}")


if __name__ == "__main__":
    # 检查Pillow是否安装
    try:
        import PIL
        print(f"Pillow 版本: {PIL.__version__}")
    except ImportError:
        print("✗ 错误：未安装 Pillow 库")
        print("请运行: pip install pillow")
        sys.exit(1)

    main()
