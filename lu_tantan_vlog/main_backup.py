import streamlit as st
import os
from config import Config
from ai_engine import generate_vlog_script
from tongyi_wanxiang_engine import TongyiWanxiangEngine
from audio_engine import generate_audio_for_script
from duration_calculator import update_script_durations, analyze_script_timing

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

# 侧边栏：系统状态和模型说明
with st.sidebar:
    st.header("⚙️ 系统状态")
    
    # 检查配置
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
    st.header("🤖 支持的 AI 模型")
    
    with st.expander("📖 模型说明"):
        st.markdown("""
        **文生视频模型 (wan2.2 系列)：**
        - `wan2.2-t2v-plus`: 直接从文本生成视频，一步到位
        
        **图生视频模型 (wan2.2 系列)：**
        - `wan2.2-i2v-plus`: 支持 prompt 引导的图片动画，效果更生动
        - ✨ 支持上传照片：在「旅行回忆」模式下可上传自己的照片
        
        **语音合成：**
        - `Edge-TTS`: 微软免费语音合成
        
        **支持的分辨率：**
        - 横屏 16:9: 1920×1080, 832×480
        - 竖屏 9:16: 1080×1920, 480×832
        - 正方形: 1440×1440, 624×624
        - 其他: 1632×1248, 1248×1632
        
        **💡 使用技巧：**
        - 旅行回忆模式：支持拖拽上传照片，AI 会让静态照片动起来
        - 建议上传 3-9 张高质量照片获得最佳效果
        """)
    
    # 配置验证
    issues = Config.validate()
    if issues:
        st.markdown("---")
        st.subheader("⚠️ 配置问题")
        for issue in issues:
            st.warning(issue)

# 主界面
st.markdown("### 🎯 创作配置")

col_mode, col_test = st.columns([3, 1])

with col_mode:
    mode = st.radio(
        "📍 内容类型：",
        ("🌟 种草攻略 (探索未知)", "📸 旅行回忆 (已游记录)"),
        key="mode",
        help="种草攻略：生成探索性内容，适合未去过的地方；旅行回忆：生成回忆性内容，适合已去过的地方"
    )

with col_test:
    st.markdown("##### 🧪 测试模式")
    test_mode = st.checkbox(
        "快速测试",
        value=False,
        help="开启后只生成1个场景，用于快速测试功能和调试",
        key="test_mode"
    )
    if test_mode:
        st.caption("⚡ 只生成1个场景")

# 初始化变量（必须在所有使用之前定义）
user_photos = []
uploaded_image_paths = []
use_uploaded_photos = False

st.markdown("### 🎨 视频生成模式")

# 如果选择了使用上传照片，自动推荐图生视频模式
if use_uploaded_photos:
    st.info("📌 检测到你要使用上传的照片，建议选择「图生视频」模式")

col1, col2 = st.columns([2, 1])

with col1:
    video_generation_mode = st.radio(
        "选择 AI 生成方式（wan2.2 系列）：",
        (
            "🎬 直接文生视频 (wan2.2-t2v-plus)",
            "🖼️ 图生视频 - 智能引导 (wan2.2-i2v-plus)"
        ),
        index=1 if use_uploaded_photos else 0,  # 如果上传照片，默认选择图生视频
        key="video_mode",
        help="""
        💡 各模式特点：
        - 直接文生视频：一步到位，文本直接生成视频，速度快
        - 图生视频(智能引导)：支持使用上传的照片或 AI 生成图片，再用 AI 让图片动起来，支持 prompt 引导运动，效果更生动
        """
    )

with col2:
    video_resolution = st.selectbox(
        "🎞️ 视频分辨率：",
        (
            "1920×1080 (横屏 16:9)",
            "1080×1920 (竖屏 9:16)",
            "1440×1440 (正方形 1:1)",
            "1632×1248 (宽屏)",
            "1248×1632 (竖屏)",
            "832×480 (横屏小)",
            "480×832 (竖屏小)",
            "624×624 (正方形小)"
        ),
        key="resolution",
        help="选择视频的输出分辨率，横屏适合电脑观看，竖屏适合手机/短视频平台"
    )
    
    # 解析分辨率
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
    selected_resolution = resolution_map[video_resolution]

location = st.text_input(
    "🗺️ 请输入旅行目的地：", 
    placeholder="例如：日本京都、云南大理、法国巴黎", 
    key="location"
)

if "旅行回忆" in mode:
    st.markdown("### 📸 上传你的旅行照片")
    
    # 添加使用上传照片的选项
    use_uploaded_photos = st.checkbox(
        "🖼️ 使用我上传的照片生成视频",
        value=False,
        help="勾选后，将使用你上传的照片配合 wan2.2-i2v-plus 图生视频模型生成动态视频"
    )
    
    if use_uploaded_photos:
        user_photos = st.file_uploader(
            "📷 拖拽或点击上传旅行照片（支持多张，推荐3-9张）",
            type=['jpg', 'png', 'jpeg'],
            accept_multiple_files=True,
            key="photos",
            help="支持拖拽上传！建议上传高质量照片，每张照片将生成一个6秒的动态视频片段"
        )
        
        if user_photos:
            st.success(f"✅ 已上传 {len(user_photos)} 张照片")
            
            # 显示上传的照片预览
            cols = st.columns(min(len(user_photos), 4))
            for idx, photo in enumerate(user_photos[:8]):  # 最多显示8张预览
                with cols[idx % 4]:
                    st.image(photo, caption=f"照片 {idx+1}", use_container_width=True)
            
            if len(user_photos) > 8:
                st.caption(f"... 还有 {len(user_photos) - 8} 张照片未显示")
            
            st.info("💡 这些照片将用于 wan2.2-i2v-plus 图生视频模型，AI 会让你的静态照片动起来！")
        else:
            st.warning("⚠️ 请上传至少1张照片，或取消勾选以使用 AI 生成内容")
    else:
        st.info("💡 未勾选使用上传照片，将使用 AI 自动生成图片内容")

# 高级选项
st.markdown("### ⚙️ 高级选项")
with st.expander("🎵 音频与字幕设置", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        enable_audio = st.checkbox("🎤 添加 AI 语音旁白", value=True, help="使用微软 Edge-TTS 免费生成中文语音")
    with col2:
        enable_subtitles = st.checkbox("📝 添加字幕", value=False, help="使用 Pillow 生成字幕，无需 ImageMagick")
    
    st.caption("💡 建议：开启语音旁白可大幅提升视频效果")
    
    # 🆕 转场效果设置
    with st.expander("🎬 视频转场设置"):
        enable_transitions = st.checkbox(
            "启用场景转场效果", 
            value=True, 
            help="在场景之间添加淡入淡出效果，使视频更流畅"
        )
        
        if enable_transitions:
            transition_duration = st.slider(
                "转场时长（秒）",
                min_value=0.2,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="场景间过渡的时长"
            )
            st.caption("✨ 开场淡入、结尾淡出、场景间交叉淡化")
        else:
            transition_duration = 0.0
            st.caption("⚠️ 关闭转场效果，场景将直接切换")
    
    # 🆕 时长计算设置
    with st.expander("⏱️ 视频时长设置（高级）"):
        st.markdown("**智能时长计算**：根据旁白文本长度自动计算每个场景的视频时长")
        
        # 🆕 视频生成限制提示
        if "文生视频" in video_generation_mode or "图生视频" in video_generation_mode:
            video_limit = 5  # 通义万相 i2v/t2v 限制
            st.warning(f"⚠️ 通义万相视频生成限制：单个场景最长 {video_limit} 秒")
            st.caption(f"💡 建议：调整语速和旁白长度，让音频时长 ≤ {video_limit} 秒，避免冻结帧")
        else:
            video_limit = 15
        
        col_a, col_b = st.columns(2)
        with col_a:
            # 根据视频限制调整默认语速（更快，以适应短视频）
            default_speed = 4.0 if video_limit == 5 else 3.5
            words_per_second = st.slider(
                "语速（字/秒）",
                min_value=3.0,
                max_value=5.5,
                value=default_speed,
                step=0.1,
                help=f"建议使用较快语速以适应 {video_limit} 秒视频限制"
            )
        with col_b:
            st.caption(f"🎯 推荐语速: {default_speed}字/秒")
            st.caption("🚀 快速: 4.5-5.5字/秒")
            st.caption("📖 标准: 3.5-4字/秒")
        
        col_c, col_d = st.columns(2)
        with col_c:
            min_scene_duration = st.number_input(
                "最短场景时长（秒）",
                min_value=1.0,
                max_value=10.0,
                value=3.0,
                step=0.5,
                help="每个场景的最短时长"
            )
        with col_d:
            max_scene_duration = st.number_input(
                "最长场景时长（秒）",
                min_value=3.0,
                max_value=float(video_limit),
                value=float(video_limit),
                step=0.5,
                help=f"受视频生成限制，最长 {video_limit} 秒"
            )
        
        st.info(f"💡 系统会将每个场景的旁白控制在 {max_scene_duration:.1f} 秒以内，确保音画同步")

# 生成按钮
st.markdown("---")
if st.button("🚀 开始生成视频", type="primary", use_container_width=True):
    if not location:
        st.error("❌ 请输入目的地！")
    elif not Config.TONGYI_API_KEY:
        st.error("❌ 请先配置通义万相 API Key")
    elif use_uploaded_photos and not user_photos:
        st.error("❌ 你选择了使用上传照片，但还没有上传任何照片！")
    elif use_uploaded_photos and "直接文生视频" in video_generation_mode:
        st.error("❌ 上传照片只能配合「图生视频」模式使用，请切换到图生视频模式")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0)
        mode_code = 'upload' if user_photos else 'guide'
        
        # 如果用户上传了照片，保存到本地
        if use_uploaded_photos and user_photos:
            status_text.text("💾 正在保存上传的照片...")
            import tempfile
            from PIL import Image
            
            for idx, uploaded_file in enumerate(user_photos):
                # 读取上传的文件
                image = Image.open(uploaded_file)
                
                # 保存到临时目录
                temp_path = os.path.join(Config.IMAGES_DIR, f"uploaded_{idx}.jpg")
                image.save(temp_path, "JPEG", quality=95)
                uploaded_image_paths.append(temp_path)
            
            st.success(f"✅ 已保存 {len(uploaded_image_paths)} 张照片")
            progress_bar.progress(5)
        
        try:
            # 步骤 1: 生成脚本
            status_text.text("🤖 正在生成 Vlog 剧本...")
            progress_bar.progress(10)
            
            script = generate_vlog_script(location, mode_code)
            
            # 测试模式：只保留第一个场景
            if test_mode and script:
                original_scene_count = len(script)
                script = [script[0]]  # 只保留第一个场景
                st.info(f"🧪 测试模式：已从 {original_scene_count} 个场景中选择第 1 个场景进行快速测试")
            
            # 🆕 根据剧本长度自动计算每个场景的时长
            st.info("⏱️ 正在根据旁白长度智能计算视频时长...")
            script = update_script_durations(
                script, 
                words_per_second=words_per_second,
                min_duration=min_scene_duration,
                max_duration=max_scene_duration
            )
            timing_analysis = analyze_script_timing(script)
            
            # 🆕 检测是否有场景超出视频生成限制
            video_gen_limit = 5 if ("文生视频" in video_generation_mode or "图生视频" in video_generation_mode) else 15
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
            
            st.success(f"✅ 已智能调整视频时长 | 总时长: {timing_analysis['total_duration']:.1f}秒 | 平均: {timing_analysis['avg_duration']:.1f}秒/场景")
            
            # 🆕 显示超限警告
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
            
            with st.expander("📝 查看生成的脚本（含智能时长）"):
                for i, scene in enumerate(script):
                    narration = scene.get('narration', '')
                    char_count = len([c for c in narration if '\u4e00' <= c <= '\u9fff'])
                    duration = scene.get('duration', 5)
                    
                    # 标记超限场景
                    if duration > video_gen_limit:
                        st.markdown(f"**场景 {i+1}**: {narration} ⚠️")
                        st.caption(f"📏 {char_count}字 → ⏱️ {duration:.1f}秒 (超出{video_gen_limit}秒限制) | 视觉: {scene.get('visual_query', '')[:50]}...")
                    else:
                        st.markdown(f"**场景 {i+1}:** {narration}")
                        st.caption(f"📏 {char_count}字 → ⏱️ {duration:.1f}秒 | 视觉: {scene.get('visual_query', '')[:50]}...")
            
            progress_bar.progress(20)
            
            engine = TongyiWanxiangEngine()
            
            # 根据选择的模式生成视频
            if "直接文生视频" in video_generation_mode:
                # 模式 1: 直接文生视频（wan2.2-t2v-plus）
                status_text.text(f"🎬 正在使用 wan2.2-t2v-plus 直接文生视频 ({video_resolution})...")
                progress_bar.progress(30)
                
                try:
                    video_paths = engine.generate_videos_from_text_direct(
                        script=script,
                        size=selected_resolution  # 使用用户选择的分辨率
                    )
                except Exception as e:
                    st.error(f"❌ 视频生成失败: {str(e)}")
                    st.warning("💡 建议：检查通义万相 API 配额，或尝试减少场景数量")
                    st.stop()
                
                # 检查生成的视频
                valid_videos = [v for v in video_paths if v and os.path.exists(v)]
                
                if not valid_videos:
                    st.error("❌ 视频生成失败")
                    st.stop()
                
                st.info(f"✅ 成功生成 {len(valid_videos)}/{len(script)} 个视频片段 (wan2.2-t2v-plus, {video_resolution})")
                progress_bar.progress(60)
                
            else:  # 图生视频 - 智能引导
                # 模式 2: 文生图 + 图生视频（wan2.2-i2v-plus，支持 prompt）
                
                # 判断是否使用上传的照片
                if use_uploaded_photos and uploaded_image_paths:
                    # 使用用户上传的照片
                    status_text.text(f"📸 使用你上传的 {len(uploaded_image_paths)} 张照片...")
                    progress_bar.progress(30)
                    
                    image_paths = uploaded_image_paths
                    
                    # 为上传的照片生成相应的脚本（根据照片数量调整）
                    if len(image_paths) < len(script):
                        # 照片少于脚本数量，截取脚本
                        script = script[:len(image_paths)]
                        st.info(f"ℹ️ 根据上传的 {len(image_paths)} 张照片，调整为生成 {len(script)} 个场景")
                    elif len(image_paths) > len(script):
                        # 照片多于脚本数量，只使用前面的照片
                        image_paths = image_paths[:len(script)]
                        st.info(f"ℹ️ 将使用前 {len(script)} 张照片生成视频")
                    
                    # 上传照片到通义万相以获取 URL（用于 wan2.2-i2v-plus）
                    # 注意：这里需要通过 OSS 上传，我们暂时使用本地路径
                    image_urls = [None] * len(image_paths)  # wan2.2-i2v-plus 支持本地路径
                    
                    st.success(f"✅ 准备使用 {len(image_paths)} 张上传的照片")
                    progress_bar.progress(45)
                    
                else:
                    # 使用 AI 生成图片
                    status_text.text(f"🎨 步骤 1/2: 使用 wanx-v1 生成图片 ({video_resolution})...")
                    progress_bar.progress(30)
                    
                    # 生成图片并获取 URL
                    image_paths, image_urls = engine.generate_images_for_script(script)
                    
                    # 检查生成的图片
                    valid_images = [img for img in image_paths if img and os.path.exists(img)]
                    
                    if not valid_images:
                        st.error("❌ 图片生成失败，请检查通义万相 API 配置")
                        st.stop()
                    
                    st.info(f"✅ 成功生成 {len(valid_images)}/{len(script)} 张图片")
                    progress_bar.progress(45)
                
                # 步骤 2: 使用 wan2.2-i2v-plus 图生视频（带 prompt 引导）
                # 注意：wan2.2-i2v-plus 生成的视频分辨率固定为 6 秒，720×1280 或 1280×720
                if use_uploaded_photos and uploaded_image_paths:
                    status_text.text(f"🎬 步骤 2/2: 使用 wan2.2-i2v-plus 让你的照片动起来...")
                    st.caption(f"ℹ️ 正在处理 {len(image_paths)} 张上传的照片，每张照片将生成 6 秒动态视频")
                else:
                    status_text.text(f"🎬 步骤 2/2: 使用 wan2.2-i2v-plus 智能图生视频（AI 引导运动）...")
                    st.caption("ℹ️ 注意：wan2.2-i2v-plus 生成固定时长 6 秒视频")
                
                try:
                    video_paths = engine.generate_videos_from_images_direct(
                        image_paths=image_paths, 
                        script=script, 
                        image_urls=image_urls,
                        use_prompt=True
                    )
                except Exception as e:
                    st.error(f"❌ 视频生成失败: {str(e)}")
                    st.warning("💡 建议：检查图片质量和通义万相 API 配额，或尝试减少场景数量")
                    st.stop()
                
                # 检查生成的视频
                valid_videos = [v for v in video_paths if v and os.path.exists(v)]
                
                if not valid_videos:
                    st.error("❌ 视频生成失败")
                    st.stop()
                
                st.info(f"✅ 成功生成 {len(valid_videos)}/{len(script)} 个视频片段 (wan2.2-i2v-plus)")
                progress_bar.progress(60)
            
            # 步骤 4: 拼接视频片段（初始版本，不延长）
            if True:  # 所有模式都需要拼接
                status_text.text("🔗 正在拼接视频片段...")
                temp_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}_temp.mp4")
                
                # 先拼接原始视频（不延长），应用转场效果
                stitch_success = engine.stitch_videos(
                    video_paths, 
                    temp_video_path, 
                    script, 
                    target_durations=None,
                    enable_transitions=enable_transitions,
                    transition_duration=transition_duration
                )
                
                if not stitch_success or not os.path.exists(temp_video_path):
                    st.error("❌ 视频拼接失败")
                    st.stop()
                
                # 临时保存为最终路径（如果不需要音频处理）
                final_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}.mp4")
            
            progress_bar.progress(75)
            
            # 步骤 5: 使用 Edge-TTS 语音合成（可选）
            if enable_audio:
                status_text.text("🎤 正在使用 Edge-TTS 生成语音旁白...")
                try:
                    # 使用 Edge-TTS 语音合成（免费且稳定）
                    from audio_engine import generate_audio_for_script
                    audio_paths = generate_audio_for_script(script, Config.AUDIO_DIR)
                    
                    # 添加音频到视频
                    valid_audio = [a for a in audio_paths if a and os.path.exists(a)]
                    
                    if valid_audio:
                        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, AudioClip
                        from moviepy.audio.AudioClip import CompositeAudioClip
                        
                        # 读取实际的视频片段时长（而不是使用剧本中的 duration）
                        st.info("📊 正在分析实际视频时长以同步音频...")
                        actual_durations = []
                        for i, video_path in enumerate(valid_videos):
                            try:
                                temp_clip = VideoFileClip(video_path)
                                actual_durations.append(temp_clip.duration)
                                temp_clip.close()
                                print(f"场景 {i+1} 实际时长: {actual_durations[-1]:.2f}秒")
                            except Exception as e:
                                print(f"⚠️ 无法读取场景 {i+1} 时长: {e}")
                                actual_durations.append(script[i].get("duration", 5))
                        
                        # 智能音频处理：延长视频场景以适应语音长度
                        from moviepy.audio.AudioClip import AudioClip as BaseAudioClip
                        
                        # 先读取所有音频时长
                        audio_durations = []
                        for audio_path in audio_paths:
                            if audio_path and os.path.exists(audio_path):
                                temp_audio = AudioFileClip(audio_path)
                                audio_durations.append(temp_audio.duration)
                                temp_audio.close()
                            else:
                                audio_durations.append(0)
                        
                        total_audio_duration = sum(audio_durations)
                        total_video_duration = sum(actual_durations)
                        
                        print(f"📊 原始 - 总音频: {total_audio_duration:.2f}秒, 总视频: {total_video_duration:.2f}秒")
                        
                        # 🔧 新功能：延长视频场景以适应语音
                        adjusted_durations = []
                        extended_count = 0
                        
                        for i, (audio_dur, video_dur) in enumerate(zip(audio_durations, actual_durations)):
                            if audio_dur > video_dur * 1.1:  # 音频超出视频 10% 以上
                                # 延长视频场景到音频长度 + 0.5秒缓冲
                                extended_dur = audio_dur + 0.5
                                adjusted_durations.append(extended_dur)
                                extended_count += 1
                                print(f"🔧 场景 {i+1} 延长: {video_dur:.2f}秒 → {extended_dur:.2f}秒 (音频 {audio_dur:.2f}秒)")
                                st.caption(f"  🔧 场景 {i+1}: 延长至 {extended_dur:.1f}秒 以匹配 {audio_dur:.1f}秒 语音")
                            else:
                                adjusted_durations.append(video_dur)
                                print(f"✅ 场景 {i+1} 保持: {video_dur:.2f}秒 (音频 {audio_dur:.2f}秒)")
                        
                        # 计算调整后的总时长
                        total_adjusted_duration = sum(adjusted_durations)
                        print(f"📊 调整后 - 总视频: {total_adjusted_duration:.2f}秒")
                        
                        if extended_count > 0:
                            st.info(f"✨ 需要延长 {extended_count} 个场景以适应语音长度")
                            
                            # 🔧 重新拼接视频，使用延长后的时长
                            status_text.text("🔧 正在延长视频以适应语音...")
                            extended_video_path = os.path.join(Config.OUTPUT_DIR, f"lu_tantan_{location}_extended.mp4")
                            
                            extend_success = engine.stitch_videos(
                                valid_videos, 
                                extended_video_path, 
                                script, 
                                target_durations=adjusted_durations,  # 传递延长后的时长
                                enable_transitions=enable_transitions,
                                transition_duration=transition_duration
                            )
                            
                            if extend_success and os.path.exists(extended_video_path):
                                # 使用延长后的视频
                                video_clip = VideoFileClip(extended_video_path)
                                st.success(f"✅ 视频已延长至 {total_adjusted_duration:.1f}秒")
                            else:
                                # 延长失败，使用原始视频
                                st.warning("⚠️ 视频延长失败，使用原始视频")
                                video_clip = VideoFileClip(temp_video_path)
                        else:
                            # 不需要延长，使用原始拼接的视频
                            video_clip = VideoFileClip(temp_video_path)
                        
                        # 🆕 保存调整后的时长供字幕使用
                        final_durations_for_subtitles = adjusted_durations.copy()
                        
                        # 现在处理音频和视频的对齐
                        audio_segments = []
                        
                        # 用于追踪需要关闭的临时音频clip
                        temp_audio_clips = []
                        
                        for i, (audio_path, audio_dur, adjusted_dur) in enumerate(zip(audio_paths, audio_durations, adjusted_durations)):
                            if audio_path and os.path.exists(audio_path) and i < len(adjusted_durations):
                                audio_clip = AudioFileClip(audio_path)
                                temp_audio_clips.append(audio_clip)
                                
                                print(f"场景 {i+1} - 音频: {audio_dur:.2f}秒, 调整后视频: {adjusted_dur:.2f}秒")
                                
                                if audio_dur < adjusted_dur:
                                    # 音频短于视频：添加静音填充
                                    silence_duration = adjusted_dur - audio_dur
                                    silence = BaseAudioClip(
                                        lambda t: [0, 0], 
                                        duration=silence_duration,
                                        fps=audio_clip.fps
                                    )
                                    segment = concatenate_audioclips([audio_clip, silence])
                                    audio_segments.append(segment)
                                    silence.close()
                                    print(f"  → 添加 {silence_duration:.2f}秒 静音")
                                else:
                                    # 时长匹配或音频稍长，直接使用
                                    audio_segments.append(audio_clip)
                                    print(f"  → 使用完整音频")
                        
                        if audio_segments:
                            # 顺序拼接所有音频片段（不会重叠）
                            final_audio = concatenate_audioclips(audio_segments)
                            video_with_audio = video_clip.set_audio(final_audio)
                            
                            audio_video_path = final_video_path.replace('.mp4', '_with_audio.mp4')
                            print("💾 正在保存带音频的视频...")
                            video_with_audio.write_videofile(
                                audio_video_path,
                                codec=Config.VIDEO_CODEC,
                                fps=Config.VIDEO_FPS,
                                audio_codec=Config.AUDIO_CODEC,
                                logger=None,  # 禁用进度条避免卡顿
                                threads=4,
                                preset='medium',
                                verbose=False
                            )
                            
                            # 清理资源（按顺序关闭）
                            print("🧹 清理音频和视频资源...")
                            try:
                                video_with_audio.close()
                            except Exception as e:
                                print(f"  ⚠️ 关闭 video_with_audio 时出错: {e}")
                            
                            try:
                                final_audio.close()
                            except Exception as e:
                                print(f"  ⚠️ 关闭 final_audio 时出错: {e}")
                            
                            # 关闭所有音频片段
                            for segment in audio_segments:
                                try:
                                    segment.close()
                                except:
                                    pass
                            
                            # 关闭所有临时音频clip
                            for temp_clip in temp_audio_clips:
                                try:
                                    temp_clip.close()
                                except:
                                    pass
                            
                            try:
                                video_clip.close()
                            except Exception as e:
                                print(f"  ⚠️ 关闭 video_clip 时出错: {e}")
                            
                            print("✅ 资源清理完成")
                            
                            if os.path.exists(audio_video_path):
                                import shutil
                                shutil.move(audio_video_path, final_video_path)
                                st.info("✅ 已添加 Edge-TTS 语音")
                            else:
                                st.warning("⚠️ 语音添加失败，保留原视频")
                        else:
                            st.warning("⚠️ 没有有效的音频文件")
                    else:
                        st.warning("⚠️ 语音生成失败，保留原视频")
                        
                except Exception as e:
                    st.warning(f"⚠️ 语音添加失败: {str(e)[:100]}")
                    import traceback
                    st.code(traceback.format_exc())
            
            progress_bar.progress(90)
            
            # 步骤 5: 添加字幕（可选）
            if enable_subtitles:
                status_text.text("📝 正在添加字幕...")
                try:
                    from subtitle_engine_v3 import add_subtitles_to_video
                    
                    subtitle_video_path = final_video_path.replace('.mp4', '_with_subtitles.mp4')
                    
                    # 🆕 使用延长后的时长（如果有音频），确保字幕与语音同步
                    if 'final_durations_for_subtitles' in locals():
                        # 已经添加了音频，使用延长后的时长
                        durations_for_subtitles = final_durations_for_subtitles
                        st.info("✅ 使用音频同步后的时长添加字幕")
                        print(f"📊 字幕时长: {durations_for_subtitles}")
                    elif 'actual_durations' in locals():
                        # 没有音频但有实际时长
                        durations_for_subtitles = actual_durations
                        st.info("📊 使用原始视频时长添加字幕")
                    else:
                        # 重新计算实际时长
                        st.info("📊 正在分析实际视频时长以同步字幕...")
                        durations_for_subtitles = []
                        for i, video_path in enumerate(valid_videos):
                            try:
                                from moviepy.editor import VideoFileClip
                                temp_clip = VideoFileClip(video_path)
                                durations_for_subtitles.append(temp_clip.duration)
                                temp_clip.close()
                            except Exception as e:
                                print(f"⚠️ 无法读取场景 {i+1} 时长: {e}")
                                durations_for_subtitles.append(script[i].get("duration", 5))
                    
                    subtitle_success = add_subtitles_to_video(
                        video_path=final_video_path,
                        script=script,
                        output_path=subtitle_video_path,
                        font_size=None,  # 使用自动计算（已减小）
                        font_color="white",
                        bg_color=None,
                        position="bottom",
                        actual_durations=durations_for_subtitles,  # 传递正确的时长
                        auto_scale=True  # 开启自动缩放
                    )
                    
                    if subtitle_success and os.path.exists(subtitle_video_path):
                        import shutil
                        shutil.move(subtitle_video_path, final_video_path)
                        st.info("✅ 已添加字幕")
                    else:
                        st.warning("⚠️ 字幕添加失败，请查看控制台日志")
                        
                except Exception as e:
                    st.warning(f"⚠️ 字幕添加失败: {str(e)[:50]}")
            
            progress_bar.progress(100)
            status_text.success("✅ Vlog 生成完毕！")
            
            # 清理临时上传的照片
            if use_uploaded_photos and uploaded_image_paths:
                for temp_path in uploaded_image_paths:
                    try:
                        if os.path.exists(temp_path) and "uploaded_" in temp_path:
                            os.remove(temp_path)
                    except Exception:
                        pass  # 忽略清理错误
            
            # 显示视频
            st.video(final_video_path)
            
            # 提供下载按钮
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

# 页脚
st.markdown("---")
st.markdown("### 📊 技术栈")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("**🤖 AI 模型 (wan2.2 系列)**")
    st.caption("wan2.2-t2v-plus (文生视频)")
    st.caption("wan2.2-i2v-plus (图生视频)")
    st.caption("支持多种分辨率")
with col2:
    st.markdown("**🎙️ 语音合成**")
    st.caption("Edge-TTS (免费)")
    st.caption("支持多种中文声音")
with col3:
    st.markdown("**🎬 视频处理**")
    st.caption("MoviePy")
    st.caption("FFmpeg")

st.markdown("---")
st.markdown("*💡 路探探 (Lu Tantan) AI 视频创作引擎 | Powered by 阿里云通义万相*")
st.caption("🔧 技术支持：多模态 AI 生成 | 智能分镜 | 自动配音 | 一键成片")
