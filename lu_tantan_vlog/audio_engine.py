"""
语音合成引擎 - 为视频添加语音旁白
"""
import os
import asyncio
import edge_tts
from typing import List, Dict


async def generate_audio_file_async(text: str, filename: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """
    使用 Edge-TTS 生成语音文件（异步）
    
    Args:
        text: 文本内容
        filename: 输出文件路径
        voice: 语音类型
            - zh-CN-XiaoxiaoNeural (女声，推荐)
            - zh-CN-YunxiNeural (男声)
            - zh-CN-YunyangNeural (男声，新闻播报)
    """
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)


def generate_audio_file(text: str, filename: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """
    使用 Edge-TTS 生成语音文件（同步）
    
    Args:
        text: 文本内容
        filename: 输出文件路径
        voice: 语音类型
    """
    asyncio.run(generate_audio_file_async(text, filename, voice))


def generate_audio_for_script(script: List[Dict], output_dir: str = "assets/audio") -> List[str]:
    """
    为整个剧本生成语音文件
    
    Args:
        script: 剧本列表，每个元素包含 'narration' 字段
        output_dir: 输出目录
    
    Returns:
        生成的音频文件路径列表
    """
    os.makedirs(output_dir, exist_ok=True)
    
    audio_paths = []
    
    for i, scene in enumerate(script):
        narration = scene.get('narration', '')
        if not narration:
            print(f"⚠️  场景 {i+1} 没有旁白，跳过")
            audio_paths.append(None)
            continue
        
        audio_path = os.path.join(output_dir, f"scene_{i}.mp3")
        
        print(f"🎤 生成语音 {i+1}/{len(script)}: {narration[:30]}...")
        
        try:
            generate_audio_file(narration, audio_path)
            audio_paths.append(audio_path)
            print(f"   ✅ 已保存到: {audio_path}")
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            audio_paths.append(None)
    
    return audio_paths


def add_audio_to_video(video_path: str, audio_paths: List[str], output_path: str) -> bool:
    """
    为视频添加音频（拼接多个音频片段）
    
    Args:
        video_path: 输入视频路径
        audio_paths: 音频文件路径列表
        output_path: 输出视频路径
    
    Returns:
        成功返回 True，失败返回 False
    """
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips
        
        print(f"🎵 正在为视频添加音频...")
        
        # 加载视频
        video = VideoFileClip(video_path)
        print(f"📹 视频时长: {video.duration:.2f} 秒")
        
        # 加载并拼接音频
        audio_clips = []
        for i, audio_path in enumerate(audio_paths):
            if audio_path and os.path.exists(audio_path):
                try:
                    audio_clip = AudioFileClip(audio_path)
                    audio_clips.append(audio_clip)
                    print(f"   ✅ 加载音频 {i+1}: {audio_clip.duration:.2f} 秒")
                except Exception as e:
                    print(f"   ⚠️  音频 {i+1} 加载失败: {e}")
        
        if not audio_clips:
            print("❌ 没有有效的音频文件")
            video.close()
            return False
        
        # 拼接所有音频
        print("🔗 正在拼接音频...")
        final_audio = concatenate_audioclips(audio_clips)
        print(f"🎵 总音频时长: {final_audio.duration:.2f} 秒")
        
        # 将音频添加到视频
        # 如果音频比视频短，视频会被裁剪
        # 如果音频比视频长，音频会被裁剪
        video_with_audio = video.set_audio(final_audio)
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入文件
        print(f"💾 正在保存到: {output_path}")
        video_with_audio.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps,
            threads=4,
            logger=None
        )
        
        # 释放资源
        for clip in audio_clips:
            clip.close()
        final_audio.close()
        video.close()
        video_with_audio.close()
        
        print(f"✅ 带音频的视频已生成: {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ 添加音频失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试
    print("测试语音合成引擎")
    
    test_script = [
        {"narration": "哈喽大家好，我是路探探！"},
        {"narration": "今天带大家探索美丽的风景！"},
    ]
    
    audio_paths = generate_audio_for_script(test_script, "assets/audio")
    print(f"\n✅ 生成了 {len([p for p in audio_paths if p])} 个音频文件")
