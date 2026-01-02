"""
字幕生成引擎 - 使用 Pillow 生成字幕
完全基于 Python 库，无需外部依赖
支持根据分辨率自动调整字幕大小
"""

import os
import platform
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def calculate_font_size_for_resolution(width: int, height: int, base_size: int = 28) -> int:
    """
    根据视频分辨率自动计算合适的字体大小
    
    Args:
        width: 视频宽度
        height: 视频高度
        base_size: 基准字体大小（用于 1920x1080，已调小）
    
    Returns:
        调整后的字体大小
    """
    # 以 1920x1080 为基准分辨率
    base_width = 1920
    base_height = 1080
    
    # 计算分辨率比例（取宽高比例的平均值）
    width_ratio = width / base_width
    height_ratio = height / base_height
    scale_ratio = (width_ratio + height_ratio) / 2
    
    # 计算调整后的字体大小（减小30%）
    adjusted_size = int(base_size * scale_ratio)
    
    # 设置合理的范围：最小 16，最大 56（整体减小）
    adjusted_size = max(16, min(56, adjusted_size))
    
    return adjusted_size


def get_recommended_subtitle_settings(width: int, height: int) -> Dict[str, int]:
    """
    根据分辨率推荐字幕设置
    
    Args:
        width: 视频宽度
        height: 视频高度
    
    Returns:
        推荐的字幕设置字典
    """
    font_size = calculate_font_size_for_resolution(width, height)
    
    # 根据字体大小计算其他参数
    settings = {
        'font_size': font_size,
        'padding': max(20, int(font_size * 0.5)),  # 边距
        'outline_width': max(2, int(font_size * 0.05)),  # 描边宽度
        'line_spacing': max(10, int(font_size * 0.25))  # 行间距
    }
    
    return settings


def get_system_font() -> Optional[str]:
    """获取系统中可用的中文字体路径"""
    system = platform.system()

    font_paths = {
        "Windows": [
            "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
            "C:/Windows/Fonts/msyhbd.ttc",  # 微软雅黑粗体
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
        ],
        "Darwin": [  # macOS
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ],
        "Linux": [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ],
    }

    for font_path in font_paths.get(system, []):
        if os.path.exists(font_path):
            return font_path

    return None


def _load_font(font_path: Optional[str], font_size: int) -> ImageFont.FreeTypeFont:
    """加载字体"""
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, font_size)
    except Exception as e:
        print(f"⚠️ 加载字体失败: {e}")

    print("⚠️ 使用默认字体")
    return ImageFont.load_default()


def _wrap_text(
    text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.Draw, max_lines: int = 2
) -> List[str]:
    """
    自动换行处理，限制最大行数
    
    Args:
        text: 要换行的文本
        font: 字体
        max_width: 最大宽度
        draw: 绘图对象
        max_lines: 最大行数（默认2行）
    
    Returns:
        换行后的文本列表
    """
    lines = []
    current_line = ""

    for i, char in enumerate(text):
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]

        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                # 如果已经达到最大行数-1，剩余文字加省略号
                if len(lines) >= max_lines:
                    remaining = text[i:]
                    # 尝试在最后一行添加尽可能多的字符
                    last_line = char
                    for next_char in remaining[1:]:
                        test_last = last_line + next_char
                        bbox = draw.textbbox((0, 0), test_last + "...", font=font)
                        if bbox[2] - bbox[0] <= max_width:
                            last_line = test_last
                        else:
                            break
                    lines.append(last_line + "...")
                    return lines
            current_line = char

    if current_line:
        lines.append(current_line)

    return lines


def _draw_text_with_outline(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: Tuple[int, int, int, int],
    outline_width: int = 2,
) -> None:
    """绘制带描边的文本"""
    x, y = position
    outline_color = (0, 0, 0, 255)

    # 绘制描边
    for adj_x in range(-outline_width, outline_width + 1):
        for adj_y in range(-outline_width, outline_width + 1):
            if adj_x != 0 or adj_y != 0:
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=outline_color)

    # 绘制主文本
    draw.text((x, y), text, font=font, fill=fill_color)


def create_subtitle_image(
    text: str,
    width: int,
    height: int,
    font_path: Optional[str] = None,
    font_size: int = 40,
    font_color: Tuple[int, int, int] = (255, 255, 255),
    bg_color: Optional[Tuple[int, int, int]] = None,
    position: str = "bottom",
    padding: int = 20,
    outline_width: int = 2,
) -> Image.Image:
    """
    使用 Pillow 创建字幕图片

    Args:
        text: 字幕文本
        width: 图片宽度
        height: 图片高度
        font_path: 字体文件路径
        font_size: 字体大小
        font_color: 字体颜色 RGB 元组
        bg_color: 背景颜色 RGB 元组，None 表示透明
        position: 字幕位置 ("bottom", "center", "top")
        padding: 文字边距

    Returns:
        PIL Image 对象
    """
    # 创建透明或有色背景
    bg = bg_color + (255,) if bg_color else (0, 0, 0, 0)
    img = Image.new("RGBA", (width, height), bg)
    draw = ImageDraw.Draw(img)

    # 加载字体
    font = _load_font(font_path, font_size)

    # 自动换行
    max_width = width - 2 * padding
    lines = _wrap_text(text, font, max_width, draw)

    # 计算文本位置
    line_height = font_size + 10
    total_height = len(lines) * line_height

    position_map = {
        "bottom": height - total_height - padding - 50,
        "center": (height - total_height) // 2,
        "top": padding + 50,
    }
    start_y = position_map.get(position, position_map["bottom"])

    # 绘制所有行
    fill_color = font_color + (255,)
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = start_y + i * line_height

        _draw_text_with_outline(draw, (x, y), line, font, fill_color, outline_width)

    return img


# 颜色映射常量
COLOR_MAP = {
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}


def _calculate_durations(
    script: List[Dict], video_duration: float, actual_durations: Optional[List[float]]
) -> Tuple[bool, float]:
    """计算场景时长调整参数"""
    if actual_durations and len(actual_durations) > 0:
        print(f"✅ 使用实际视频片段时长列表（{len(actual_durations)} 个片段）")
        return True, 1.0

    script_total = sum(scene.get("duration", 5) for scene in script)
    print(f"📝 剧本总时长: {script_total:.2f} 秒")

    if abs(script_total - video_duration) > 1.0:
        scale = video_duration / script_total
        print(f"⚠️  剧本时长与视频时长不匹配，调整系数: {scale:.2f}")
        return False, scale

    return False, 1.0


def add_subtitles_to_video(
    video_path: str,
    script: List[Dict],
    output_path: str,
    font: Optional[str] = None,
    font_size: Optional[int] = None,
    font_color: str = "white",
    bg_color: Optional[str] = None,
    position: str = "bottom",
    actual_durations: Optional[List[float]] = None,
    auto_scale: bool = True,
) -> bool:
    """
    为视频添加硬编码字幕

    Args:
        video_path: 输入视频路径
        script: 剧本列表，每个场景包含 narration 和 duration
        output_path: 输出视频路径
        font: 字体路径，None 则自动检测系统字体
        font_size: 字体大小，None 则根据分辨率自动计算
        font_color: 字体颜色名称
        bg_color: 背景颜色名称，None 表示透明
        position: 字幕位置 ("bottom", "center", "top")
        actual_durations: 实际视频片段时长列表
        auto_scale: 是否根据分辨率自动调整字幕大小

    Returns:
        成功返回 True，失败返回 False
    """
    try:
        from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

        print(f"📹 正在为视频添加字幕...")

        # 获取字体
        if font is None:
            font = get_system_font()
            if font:
                print(f"✅ 使用系统字体: {os.path.basename(font)}")
            else:
                print("⚠️ 未找到系统字体，将使用默认字体")

        # 转换颜色
        font_color_rgb = COLOR_MAP.get(font_color.lower(), (255, 255, 255))
        bg_color_rgb = COLOR_MAP.get(bg_color.lower()) if bg_color else None

        # 加载视频
        video = VideoFileClip(video_path)
        print(f"📊 视频信息: {video.w}x{video.h}, {video.duration:.2f}秒")
        
        # 🆕 根据分辨率自动调整字幕大小
        if auto_scale and font_size is None:
            settings = get_recommended_subtitle_settings(video.w, video.h)
            font_size = settings['font_size']
            padding = settings['padding']
            outline_width = settings['outline_width']
            print(f"🎨 自动调整字幕: 字体 {font_size}px, 边距 {padding}px, 描边 {outline_width}px")
        else:
            # 使用指定的字体大小或默认值
            font_size = font_size or 40
            padding = 20
            outline_width = 2
            print(f"🎨 使用固定字幕大小: {font_size}px")
        
        print(f"📋 剧本场景数: {len(script)}")

        # 计算时长调整
        use_actual, scale_factor = _calculate_durations(
            script, video.duration, actual_durations
        )

        # 创建字幕片段
        subtitle_clips = []
        current_time = 0.0

        for i, scene in enumerate(script):
            narration = scene.get("narration", "")
            if not narration:
                continue

            # 计算时长
            if use_actual and i < len(actual_durations):
                duration = actual_durations[i]
                print(f"  📊 场景 {i+1} 使用实际时长: {duration:.2f}秒")
            else:
                duration = scene.get("duration", 5) * scale_factor
                print(f"  📊 场景 {i+1} 使用剧本时长: {duration:.2f}秒 (缩放系数: {scale_factor:.2f})")

            # 边界检查
            if current_time >= video.duration:
                break
            if current_time + duration > video.duration:
                duration = video.duration - current_time

            print(f"  ➕ 添加字幕 {i+1}: {narration[:30]}...")

            try:
                # 创建字幕图片
                subtitle_img = create_subtitle_image(
                    text=narration,
                    width=video.w,
                    height=video.h,
                    font_path=font,
                    font_size=font_size,
                    font_color=font_color_rgb,
                    bg_color=bg_color_rgb,
                    position=position,
                    padding=padding,
                )

                # 转换为 MoviePy clip
                subtitle_clip = ImageClip(np.array(subtitle_img), transparent=True)
                subtitle_clip = subtitle_clip.set_duration(duration).set_start(
                    current_time
                )
                subtitle_clips.append(subtitle_clip)

                print(f"     ✅ 字幕 {i+1} 创建成功")

            except Exception as e:
                print(f"     ⚠️  字幕 {i+1} 创建失败: {e}")
                continue

            current_time += duration

        if not subtitle_clips:
            print("❌ 没有成功创建任何字幕")
            video.close()
            return False

        # 合成视频
        print("🔗 正在合成视频和字幕...")
        final_video = CompositeVideoClip([video] + subtitle_clips)

        # 保存
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        print(f"💾 正在保存到: {output_path}")
        final_video.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps,
            threads=4,
            logger=None,
        )

        # 清理资源
        for clip in subtitle_clips:
            clip.close()
        final_video.close()
        video.close()

        print(f"✅ 带字幕的视频已生成: {output_path}")
        return True

    except Exception as e:
        print(f"❌ 添加字幕失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("字幕引擎测试")
    print("=" * 50)

    font = get_system_font()
    print(f"✅ 系统字体: {font or '默认字体'}\n")

    # 测试创建字幕图片
    try:
        img = create_subtitle_image(
            text="这是一段测试字幕文本，用于验证字幕生成功能是否正常工作。",
            width=1280,
            height=720,
            font_path=font,
            font_size=36,
            font_color=(255, 255, 255),
            position="bottom",
        )

        test_output = "assets/output/test_subtitle.png"
        os.makedirs(os.path.dirname(test_output), exist_ok=True)
        img.save(test_output)
        print(f"✅ 字幕图片生成成功: {test_output}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
