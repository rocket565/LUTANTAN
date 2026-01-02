"""
UI Helper Functions - 辅助函数模块
将 main.py 中的复杂逻辑提取到独立函数中
"""
import os
import streamlit as st
from typing import List, Dict, Tuple, Optional
from PIL import Image


def save_uploaded_photos(user_photos, images_dir: str) -> List[str]:
    """
    保存用户上传的照片到本地
    
    Args:
        user_photos: Streamlit 上传的文件列表
        images_dir: 图片保存目录
    
    Returns:
        保存后的图片路径列表
    """
    uploaded_image_paths = []
    
    for idx, uploaded_file in enumerate(user_photos):
        image = Image.open(uploaded_file)
        temp_path = os.path.join(images_dir, f"uploaded_{idx}.jpg")
        image.save(temp_path, "JPEG", quality=95)
        uploaded_image_paths.append(temp_path)
    
    return uploaded_image_paths


def cleanup_temp_files(file_paths: List[str], pattern: str = "uploaded_"):
    """
    清理临时文件
    
    Args:
        file_paths: 文件路径列表
        pattern: 文件名模式，只删除匹配的文件
    """
    for temp_path in file_paths:
        try:
            if os.path.exists(temp_path) and pattern in temp_path:
                os.remove(temp_path)
        except Exception:
            pass  # 忽略清理错误


def get_resolution_settings() -> Tuple[Dict[str, str], List[str]]:
    """
    获取分辨率配置
    
    Returns:
        (分辨率映射字典, 分辨率选项列表)
    """
    resolution_map = {
        "1920×1080 (横屏 16:9)": "1920*1080",
        "1080×1920 (竖屏 9:16)": "1080*1920",
        "1440×1440 (正方形 1:1)": "1440*1440",
        "1632×1248 (宽屏)": "1632*1248",
        "1248×1632 (竖屏)": "1248*1632",
        "832×480 (横屏小)": "832*480",
        "480×832 (竖屏小)": "480*832",
        "624×624 (正方形小)": "624*624"
    }
    
    resolution_options = list(resolution_map.keys())
    
    return resolution_map, resolution_options


def display_timing_analysis(script: List[Dict], video_gen_limit: int, words_per_second: float):
    """
    显示时长分析和超限场景警告
    
    Args:
        script: 剧本列表
        video_gen_limit: 视频生成限制（秒）
        words_per_second: 语速（字/秒）
    """
    over_limit_scenes = []
    
    for i, scene in enumerate(script):
        duration = scene.get('duration', 5)
        if duration > video_gen_limit:
            narration = scene.get('narration', '')
            char_count = len([c for c in narration if '\u4e00' <= c <= '\u9fff'])
            over_limit_scenes.append({
                'index': i + 1,
                'duration': duration,
                'char_count': char_count,
                'narration': narration[:30] + '...'
            })
    
    if over_limit_scenes:
        st.warning(f"⚠️ {len(over_limit_scenes)} 个场景超出 {video_gen_limit}秒限制，生成时将使用冻结帧延长")
        with st.expander(f"⚡ 查看超限场景（点击展开优化建议）"):
            for scene_info in over_limit_scenes:
                st.markdown(f"**场景 {scene_info['index']}**: {scene_info['narration']}")
                st.caption(f"   当前: {scene_info['char_count']}字 → {scene_info['duration']:.1f}秒 | 建议: ≤{int(video_gen_limit * words_per_second)}字")
            
            st.info(f"💡 优化建议：")
            st.markdown(f"""
            - 🔧 **提高语速**: 当前 {words_per_second:.1f}字/秒 → 建议 4.5-5字/秒
            - ✂️ **精简旁白**: 每个场景控制在 {int(video_gen_limit * words_per_second)}字以内
            - 🎯 **建议字数**: {int(video_gen_limit * 4)}字（4字/秒） 或 {int(video_gen_limit * 5)}字（5字/秒）
            """)


def display_script_preview(script: List[Dict], video_gen_limit: int):
    """
    显示脚本预览
    
    Args:
        script: 剧本列表
        video_gen_limit: 视频生成限制（秒）
    """
    with st.expander("📝 查看生成的脚本（含智能时长）"):
        for i, scene in enumerate(script):
            narration = scene.get('narration', '')
            char_count = len([c for c in narration if '\u4e00' <= c <= '\u9fff'])
            duration = scene.get('duration', 5)
            
            if duration > video_gen_limit:
                st.markdown(f"**场景 {i+1}**: {narration} ⚠️")
                st.caption(f"📏 {char_count}字 → ⏱️ {duration:.1f}秒 (超出{video_gen_limit}秒限制) | 视觉: {scene.get('visual_query', '')[:50]}...")
            else:
                st.markdown(f"**场景 {i+1}:** {narration}")
                st.caption(f"📏 {char_count}字 → ⏱️ {duration:.1f}秒 | 视觉: {scene.get('visual_query', '')[:50]}...")


def validate_generation_params(location: str, tongyi_configured: bool, 
                               use_uploaded_photos: bool, user_photos, 
                               video_mode: str) -> Tuple[bool, Optional[str]]:
    """
    验证生成参数
    
    Returns:
        (是否验证通过, 错误消息)
    """
    if not location:
        return False, "❌ 请输入目的地！"
    
    if not tongyi_configured:
        return False, "❌ 请先配置通义万相 API Key"
    
    if use_uploaded_photos and not user_photos:
        return False, "❌ 你选择了使用上传照片，但还没有上传任何照片！"
    
    if use_uploaded_photos and "直接文生视频" in video_mode:
        return False, "❌ 上传照片只能配合「图生视频」模式使用，请切换到图生视频模式"
    
    return True, None


def display_photo_preview(user_photos, max_display: int = 8):
    """
    显示照片预览网格
    
    Args:
        user_photos: 上传的照片列表
        max_display: 最多显示的照片数量
    """
    cols = st.columns(min(len(user_photos), 4))
    for idx, photo in enumerate(user_photos[:max_display]):
        with cols[idx % 4]:
            st.image(photo, caption=f"照片 {idx+1}", use_container_width=True)
    
    if len(user_photos) > max_display:
        st.caption(f"... 还有 {len(user_photos) - max_display} 张照片未显示")
