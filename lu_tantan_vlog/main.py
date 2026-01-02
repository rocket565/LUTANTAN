"""
优化后的主界面 - 路探探 AI Vlog 生成器
主要优化：
1. UI 简化：根据模型选择自动显示/隐藏图片上传功能
2. 代码结构：提取辅助函数，减少重复代码
3. 逻辑优化：简化条件判断，提升用户体验
"""
import streamlit as st
import os
from config import Config
from ai_engine import generate_vlog_script
from tongyi_wanxiang_engine import TongyiWanxiangEngine
from audio_engine import generate_audio_for_script
from duration_calculator import update_script_durations, analyze_script_timing
from script_styles import get_all_styles, get_style_description
from ui_helpers import (
    save_uploaded_photos, 
    cleanup_temp_files,
    get_resolution_settings,
    display_timing_analysis,
    display_script_preview,
    validate_generation_params,
    display_photo_preview
)

# 确保必要的目录存在
Config.ensure_dirs()

# 设置页面配置
st.set_page_config(
    page_title="路探探 AI Vlog 生成器", 
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🎬 AI 智能视频生成工作台")
st.subheader("路探探 (Lu Tantan) - 多模态 AI 视频创作引擎")
st.caption("💡 集成阿里云通义万相多模型 | 智能分镜 | AI 配音 | 一键成片")

# ==================== 侧边栏：系统状态 ====================
with st.sidebar:
    st.header("⚙️ 系统状态")
    
    status = Config.get_status()
    
    if status["tongyi_configured"]:
        st.success("✅ 通义万相 API 已配置")
    else:
        st.error("❌ 通义万相 API 未配置")
        st.info("请在 .env 文件中设置 TONGYI_API_KEY")
    
    if status["openai_configured"]:
        st.success("✅ OpenAI API 已配置")
        st.caption("将使用 AI 生成个性化剧本")
    else:
        st.warning("⚠️ OpenAI API 未配置")
        st.caption("将使用默认剧本模板")
    
    st.markdown("---")
    st.header("🤖 模型说明")
    
    with st.expander("📖 查看详情", expanded=False):
        st.markdown("""
        **文生视频 (T2V)：**
        - `wan2.2-t2v-plus`: 文本直接生成视频
        - ⚡ 速度快，一步到位
        
        **图生视频 (I2V)：**
        - `wan2.2-i2v-plus`: 图片动画化
        - 🖼️ 支持上传照片或 AI 生成
        - ✨ 支持 prompt 引导运动
        
        **支持分辨率：**
        横屏、竖屏、正方形等多种规格
        """)
    
    # 配置问题提示
    issues = Config.validate()
    if issues:
        st.markdown("---")
        st.subheader("⚠️ 配置问题")
        for issue in issues:
            st.warning(issue)

# ==================== 主界面：创作配置 ====================
st.markdown("### 🎯 创作配置")

col_mode, col_test = st.columns([3, 1])

with col_mode:
    mode = st.radio(
        "📍 内容类型：",
        ("🌟 种草攻略 (探索未知)", "📸 旅行回忆 (已游记录)"),
        key="mode",
        help="种草攻略：生成探索性内容；旅行回忆：生成回忆性内容"
    )

with col_test:
    st.markdown("##### 🧪 测试模式")
    test_mode = st.checkbox(
        "快速测试",
        value=False,
        help="只生成1个场景，快速测试",
        key="test_mode"
    )
    if test_mode:
        st.caption("⚡ 只生成1个场景")

# 目的地输入
location = st.text_input(
    "🗺️ 请输入旅行目的地：", 
    placeholder="例如：日本京都、云南大理、法国巴黎", 
    key="location"
)

# ==================== 剧本风格选择 ====================
st.markdown("### 🎭 剧本风格")

# 获取所有可用风格
all_styles = get_all_styles()
style_options = [display_name for display_name, _ in all_styles]
style_names = {display_name: name for display_name, name in all_styles}

col_style1, col_style2 = st.columns([2, 1])

with col_style1:
    selected_style_display = st.selectbox(
        "选择视频风格：",
        style_options,
        key="script_style",
        help="不同风格会影响旁白语气、叙事节奏和视觉氛围"
    )
    selected_style = style_names[selected_style_display]

with col_style2:
    st.markdown("##### 风格说明")
    st.caption(get_style_description(selected_style))

# ==================== 视频生成模式选择 ====================
st.markdown("### 🎨 视频生成模式")

# 获取分辨率配置
resolution_map, resolution_options = get_resolution_settings()

col1, col2 = st.columns([2, 1])

with col1:
    video_generation_mode = st.radio(
        "选择 AI 生成方式：",
        (
            "🎬 文生视频 (T2V) - 一步到位",
            "🖼️ 图生视频 (I2V) - 照片动画化"
        ),
        key="video_mode",
        help="""
        💡 模式说明：
        - 文生视频：文本直接生成视频，速度快
        - 图生视频：可上传照片或 AI 生成图片，再转为视频，效果更生动
        """
    )

with col2:
    video_resolution = st.selectbox(
        "🎞️ 视频分辨率：",
        resolution_options,
        key="resolution",
        help="选择视频输出分辨率"
    )
    selected_resolution = resolution_map[video_resolution]

# ==================== 图生视频模式：照片上传 ====================
user_photos = []
use_uploaded_photos = False

# 只有在图生视频模式下才显示照片上传选项
if "图生视频" in video_generation_mode:
    st.markdown("### 📸 图片来源")
    
    image_source = st.radio(
        "选择图片来源：",
        ("🤖 AI 自动生成图片", "📷 使用我的照片"),
        key="image_source",
        horizontal=True,
        help="AI生成：系统自动生成场景图片；使用照片：上传你的旅行照片"
    )
    
    if image_source == "📷 使用我的照片":
        use_uploaded_photos = True
        
        user_photos = st.file_uploader(
            "📷 拖拽或点击上传旅行照片（支持多张，推荐3-9张）",
            type=['jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key="photos",
            help="每张照片将生成一个动态视频片段"
        )
        
        if user_photos:
            st.success(f"✅ 已上传 {len(user_photos)} 张照片")
            display_photo_preview(user_photos)
            st.info("💡 AI 会让你的静态照片动起来！")
        else:
            st.warning("⚠️ 请上传至少1张照片")
    else:
        st.info("💡 系统将使用 AI 自动生成场景图片")

# ==================== 高级选项 ====================
st.markdown("### ⚙️ 高级选项")

with st.expander("🎵 音频与字幕", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        enable_audio = st.checkbox("🎤 添加 AI 语音旁白", value=True, help="使用微软 Edge-TTS 生成")
    with col2:
        enable_subtitles = st.checkbox("📝 添加字幕", value=False, help="自动生成字幕")
    
    st.caption("💡 建议：开启语音旁白可大幅提升视频效果")

with st.expander("🎬 转场效果", expanded=False):
    enable_transitions = st.checkbox(
        "启用场景转场效果", 
        value=True, 
        help="场景间添加淡入淡出"
    )
    
    if enable_transitions:
        transition_duration = st.slider(
            "转场时长（秒）",
            min_value=0.2,
            max_value=1.0,
            value=0.5,
            step=0.1
        )
        st.caption("✨ 开场淡入、结尾淡出、场景间交叉淡化")
    else:
        transition_duration = 0.0
        st.caption("⚠️ 场景将直接切换")

with st.expander("⏱️ 视频时长设置", expanded=False):
    st.markdown("**智能时长计算**：根据旁白长度自动计算场景时长")
    
    # 根据模式设置视频限制
    video_limit = 5  # 通义万相限制
    st.warning(f"⚠️ 通义万相限制：单场景最长 {video_limit} 秒")
    st.caption(f"💡 建议：调整语速和旁白长度，避免冻结帧")
    
    col_a, col_b = st.columns(2)
    with col_a:
        default_speed = 4.0
        words_per_second = st.slider(
            "语速（字/秒）",
            min_value=3.0,
            max_value=5.5,
            value=default_speed,
            step=0.1,
            help=f"建议使用较快语速以适应 {video_limit} 秒限制"
        )
    with col_b:
        st.caption(f"🎯 推荐: {default_speed}字/秒")
        st.caption("🚀 快速: 4.5-5.5字/秒")
        st.caption("📖 标准: 3.5-4字/秒")
    
    col_c, col_d = st.columns(2)
    with col_c:
        min_scene_duration = st.number_input(
            "最短场景时长（秒）",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5
        )
    with col_d:
        max_scene_duration = st.number_input(
            "最长场景时长（秒）",
            min_value=3.0,
            max_value=float(video_limit),
            value=float(video_limit),
            step=0.5
        )

# ==================== 生成按钮 ====================
st.markdown("---")
if st.button("🚀 开始生成视频", type="primary", use_container_width=True):
    # 验证参数
    is_valid, error_msg = validate_generation_params(
        location, 
        status["tongyi_configured"],
        use_uploaded_photos,
        user_photos,
        video_generation_mode
    )
    
    if not is_valid:
        st.error(error_msg)
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        uploaded_image_paths = []
        
        # 保存上传的照片
        if use_uploaded_photos and user_photos:
            status_text.text("💾 正在保存上传的照片...")
            uploaded_image_paths = save_uploaded_photos(user_photos, Config.IMAGES_DIR)
            st.success(f"✅ 已保存 {len(uploaded_image_paths)} 张照片")
            progress_bar.progress(5)
        
        try:
            # 步骤 1: 生成脚本
            status_text.text(f"🤖 正在生成 Vlog 剧本（风格：{selected_style}）...")
            progress_bar.progress(10)
            
            mode_code = 'upload' if user_photos else 'guide'
            script = generate_vlog_script(location, mode_code, style_name=selected_style)
            
            # 测试模式处理
            if test_mode and script:
                original_scene_count = len(script)
                script = [script[0]]
                st.info(f"🧪 测试模式：已从 {original_scene_count} 个场景中选择第 1 个场景")
            
            # 智能计算时长
            st.info("⏱️ 正在根据旁白长度智能计算视频时长...")
            script = update_script_durations(
                script, 
                words_per_second=words_per_second,
                min_duration=min_scene_duration,
                max_duration=max_scene_duration
            )
            timing_analysis = analyze_script_timing(script)
            
            st.success(f"✅ 已智能调整视频时长 | 总时长: {timing_analysis['total_duration']:.1f}秒 | 平均: {timing_analysis['avg_duration']:.1f}秒/场景")
            
            # 显示时长分析
            display_timing_analysis(script, video_limit, words_per_second)
            
            # 显示脚本预览
            display_script_preview(script, video_limit)
            
            progress_bar.progress(20)
            
            engine = TongyiWanxiangEngine()
            
            # 步骤 2: 生成视频
            if "文生视频" in video_generation_mode:
                # 文生视频模式
                status_text.text(f"🎬 正在使用 T2V 直接生成视频 ({video_resolution})...")
                progress_bar.progress(30)
                
                try:
                    video_paths = engine.generate_videos_from_text_direct(
                        script=script,
                        size=selected_resolution
                    )
                except Exception as e:
                    st.error(f"❌ 视频生成失败: {str(e)}")
                    st.warning("💡 建议：检查 API 配额或减少场景数量")
                    st.stop()
                
                valid_videos = [v for v in video_paths if v and os.path.exists(v)]
                
                if not valid_videos:
                    st.error("❌ 视频生成失败")
                    st.stop()
                
                st.info(f"✅ 成功生成 {len(valid_videos)}/{len(script)} 个视频片段")
                progress_bar.progress(60)
                
            else:
                # 图生视频模式
                if use_uploaded_photos and uploaded_image_paths:
                    # 使用上传的照片
                    status_text.text(f"📸 使用你上传的 {len(uploaded_image_paths)} 张照片...")
                    progress_bar.progress(30)
                    
                    image_paths = uploaded_image_paths
                    
                    # 调整脚本数量
                    if len(image_paths) < len(script):
                        script = script[:len(image_paths)]
                        st.info(f"ℹ️ 根据 {len(image_paths)} 张照片，生成 {len(script)} 个场景")
                    elif len(image_paths) > len(script):
                        image_paths = image_paths[:len(script)]
                        st.info(f"ℹ️ 将使用前 {len(script)} 张照片")
                    
                    image_urls = [None] * len(image_paths)
                    st.success(f"✅ 准备使用 {len(image_paths)} 张照片")
                    progress_bar.progress(45)
                    
                else:
                    # AI 生成图片
                    status_text.text(f"🎨 步骤 1/2: AI 生成图片 ({video_resolution})...")
                    progress_bar.progress(30)
                    
                    image_paths, image_urls = engine.generate_images_for_script(script)
                    
                    valid_images = [img for img in image_paths if img and os.path.exists(img)]
                    
                    if not valid_images:
                        st.error("❌ 图片生成失败")
                        st.stop()
                    
                    st.info(f"✅ 成功生成 {len(valid_images)}/{len(script)} 张图片")
                    progress_bar.progress(45)
                
                # 图生视频
                status_text.text(f"🎬 步骤 2/2: I2V 让图片动起来...")
                st.caption("ℹ️ 生成 6 秒动态视频")
                
                try:
                    video_paths = engine.generate_videos_from_images_direct(
                        image_paths=image_paths, 
                        script=script, 
                        image_urls=image_urls,
                        use_prompt=True
                    )
                except Exception as e:
                    st.error(f"❌ 视频生成失败: {str(e)}")
                    st.warning("💡 建议：检查图片质量和 API 配额")
                    st.stop()
                
                valid_videos = [v for v in video_paths if v and os.path.exists(v)]
                
                if not valid_videos:
                    st.error("❌ 视频生成失败")
                    st.stop()
                
                st.info(f"✅ 成功生成 {len(valid_videos)}/{len(script)} 个视频片段")
                progress_bar.progress(60)
            
            # 步骤 3: 拼接视频
            status_text.text("🔗 正在拼接视频片段...")
            temp_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}_temp.mp4")
            
            stitch_success = engine.stitch_videos(
                valid_videos, 
                temp_video_path, 
                script, 
                target_durations=None,
                enable_transitions=enable_transitions,
                transition_duration=transition_duration
            )
            
            if not stitch_success or not os.path.exists(temp_video_path):
                st.error("❌ 视频拼接失败")
                st.stop()
            
            final_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}.mp4")
            
            progress_bar.progress(75)
            
            # 步骤 4: 添加音频（可选）
            if enable_audio:
                status_text.text("🎤 正在生成 AI 语音旁白...")
                try:
                    audio_paths = generate_audio_for_script(script, Config.AUDIO_DIR)
                    valid_audio = [a for a in audio_paths if a and os.path.exists(a)]
                    
                    if valid_audio:
                        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
                        from moviepy.audio.AudioClip import AudioClip as BaseAudioClip
                        
                        # 读取实际视频时长
                        st.info("📊 正在分析视频时长以同步音频...")
                        actual_durations = []
                        for i, video_path in enumerate(valid_videos):
                            try:
                                temp_clip = VideoFileClip(video_path)
                                actual_durations.append(temp_clip.duration)
                                temp_clip.close()
                            except Exception as e:
                                actual_durations.append(script[i].get("duration", 5))
                        
                        # 读取音频时长
                        audio_durations = []
                        for audio_path in audio_paths:
                            if audio_path and os.path.exists(audio_path):
                                temp_audio = AudioFileClip(audio_path)
                                audio_durations.append(temp_audio.duration)
                                temp_audio.close()
                            else:
                                audio_durations.append(0)
                        
                        # 计算调整后的时长
                        adjusted_durations = []
                        extended_count = 0
                        
                        for i, (audio_dur, video_dur) in enumerate(zip(audio_durations, actual_durations)):
                            if audio_dur > video_dur * 1.1:
                                extended_dur = audio_dur + 0.5
                                adjusted_durations.append(extended_dur)
                                extended_count += 1
                                st.caption(f"  🔧 场景 {i+1}: 延长至 {extended_dur:.1f}秒 匹配 {audio_dur:.1f}秒 语音")
                            else:
                                adjusted_durations.append(video_dur)
                        
                        # 如果需要延长，重新拼接
                        if extended_count > 0:
                            st.info(f"✨ 延长 {extended_count} 个场景以适应语音")
                            status_text.text("🔧 正在延长视频以适应语音...")
                            
                            extended_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}_extended.mp4")
                            
                            extend_success = engine.stitch_videos(
                                valid_videos, 
                                extended_video_path, 
                                script, 
                                target_durations=adjusted_durations,
                                enable_transitions=enable_transitions,
                                transition_duration=transition_duration
                            )
                            
                            if extend_success and os.path.exists(extended_video_path):
                                video_clip = VideoFileClip(extended_video_path)
                                st.success(f"✅ 视频已延长至 {sum(adjusted_durations):.1f}秒")
                            else:
                                st.warning("⚠️ 视频延长失败，使用原视频")
                                video_clip = VideoFileClip(temp_video_path)
                        else:
                            video_clip = VideoFileClip(temp_video_path)
                        
                        # 保存时长供字幕使用
                        final_durations_for_subtitles = adjusted_durations.copy()
                        
                        # 处理音频
                        audio_segments = []
                        temp_audio_clips = []
                        
                        for i, (audio_path, audio_dur, adjusted_dur) in enumerate(zip(audio_paths, audio_durations, adjusted_durations)):
                            if audio_path and os.path.exists(audio_path) and i < len(adjusted_durations):
                                audio_clip = AudioFileClip(audio_path)
                                temp_audio_clips.append(audio_clip)
                                
                                if audio_dur < adjusted_dur:
                                    # 添加静音
                                    silence_duration = adjusted_dur - audio_dur
                                    silence = BaseAudioClip(
                                        lambda t: [0, 0], 
                                        duration=silence_duration,
                                        fps=audio_clip.fps
                                    )
                                    segment = concatenate_audioclips([audio_clip, silence])
                                    audio_segments.append(segment)
                                    silence.close()
                                else:
                                    audio_segments.append(audio_clip)
                        
                        if audio_segments:
                            final_audio = concatenate_audioclips(audio_segments)
                            video_with_audio = video_clip.set_audio(final_audio)
                            
                            audio_video_path = final_video_path.replace('.mp4', '_with_audio.mp4')
                            video_with_audio.write_videofile(
                                audio_video_path,
                                codec=Config.VIDEO_CODEC,
                                fps=Config.VIDEO_FPS,
                                audio_codec=Config.AUDIO_CODEC,
                                logger=None,
                                threads=4,
                                preset='medium',
                                verbose=False
                            )
                            
                            # 清理资源
                            video_with_audio.close()
                            final_audio.close()
                            for segment in audio_segments:
                                try:
                                    segment.close()
                                except:
                                    pass
                            for temp_clip in temp_audio_clips:
                                try:
                                    temp_clip.close()
                                except:
                                    pass
                            video_clip.close()
                            
                            if os.path.exists(audio_video_path):
                                import shutil
                                shutil.move(audio_video_path, final_video_path)
                                st.info("✅ 已添加语音")
                            else:
                                st.warning("⚠️ 语音添加失败")
                        else:
                            st.warning("⚠️ 没有有效音频")
                    else:
                        st.warning("⚠️ 语音生成失败")
                        
                except Exception as e:
                    st.warning(f"⚠️ 语音添加失败: {str(e)[:100]}")
            
            progress_bar.progress(90)
            
            # 步骤 5: 添加字幕（可选）
            if enable_subtitles:
                status_text.text("📝 正在添加字幕...")
                try:
                    from subtitle_engine_v3 import add_subtitles_to_video
                    
                    subtitle_video_path = final_video_path.replace('.mp4', '_with_subtitles.mp4')
                    
                    # 使用正确的时长
                    if 'final_durations_for_subtitles' in locals():
                        durations_for_subtitles = final_durations_for_subtitles
                        st.info("✅ 使用音频同步后的时长")
                    elif 'actual_durations' in locals():
                        durations_for_subtitles = actual_durations
                        st.info("📊 使用原始视频时长")
                    else:
                        durations_for_subtitles = []
                        for i, video_path in enumerate(valid_videos):
                            try:
                                temp_clip = VideoFileClip(video_path)
                                durations_for_subtitles.append(temp_clip.duration)
                                temp_clip.close()
                            except Exception:
                                durations_for_subtitles.append(script[i].get("duration", 5))
                    
                    subtitle_success = add_subtitles_to_video(
                        video_path=final_video_path,
                        script=script,
                        output_path=subtitle_video_path,
                        font_size=None,
                        font_color="white",
                        bg_color=None,
                        position="bottom",
                        actual_durations=durations_for_subtitles,
                        auto_scale=True
                    )
                    
                    if subtitle_success and os.path.exists(subtitle_video_path):
                        import shutil
                        shutil.move(subtitle_video_path, final_video_path)
                        st.info("✅ 已添加字幕")
                    else:
                        st.warning("⚠️ 字幕添加失败")
                        
                except Exception as e:
                    st.warning(f"⚠️ 字幕添加失败: {str(e)[:50]}")
            
            progress_bar.progress(100)
            status_text.success("✅ Vlog 生成完毕！")
            
            # 清理临时文件
            cleanup_temp_files(uploaded_image_paths)
            
            # 显示视频
            st.video(final_video_path)
            
            # 下载按钮
            with open(final_video_path, "rb") as file:
                st.download_button(
                    label="📥 下载视频",
                    data=file,
                    file_name=f"lu_tantan_{location}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
        
        except Exception as e:
            progress_bar.progress(0)
            st.error(f"❌ 发生错误: {str(e)}")
            
            with st.expander("查看错误详情"):
                import traceback
                st.code(traceback.format_exc())

# ==================== 页脚 ====================
st.markdown("---")
st.markdown("### 📊 技术栈")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🤖 AI 模型**")
    st.caption("通义万相 T2V/I2V")
with col2:
    st.markdown("**🎙️ 语音合成**")
    st.caption("Edge-TTS (免费)")
with col3:
    st.markdown("**🎬 视频处理**")
    st.caption("MoviePy + FFmpeg")

st.markdown("---")
st.markdown("*💡 路探探 AI 视频创作引擎 | Powered by 阿里云通义万相*")
