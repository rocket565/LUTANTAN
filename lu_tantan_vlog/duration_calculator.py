"""
时长计算器 - 根据剧本内容自动计算视频时长
"""
from typing import List, Dict


def calculate_narration_duration(text: str, words_per_second: float = 3.5) -> float:
    """
    根据旁白文本计算所需时长
    
    Args:
        text: 旁白文本
        words_per_second: 每秒字数（中文平均语速：3-4字/秒，考虑停顿为3.5）
    
    Returns:
        所需秒数
    """
    # 移除标点和空格，计算实际字数
    chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    
    # 计算基础时长
    base_duration = chinese_chars / words_per_second
    
    # 添加缓冲时间（10%），确保语音不会太赶
    buffer_duration = base_duration * 0.1
    
    # 设置最小和最大时长限制
    min_duration = 3.0  # 最短3秒
    max_duration = 15.0  # 最长15秒
    
    final_duration = base_duration + buffer_duration
    final_duration = max(min_duration, min(max_duration, final_duration))
    
    return round(final_duration, 1)


def calculate_scene_durations(script: List[Dict], 
                               words_per_second: float = 3.5,
                               min_duration: float = 3.0,
                               max_duration: float = 15.0) -> List[float]:
    """
    为整个剧本计算每个场景的时长
    
    Args:
        script: 剧本列表，每个场景包含 'narration' 字段
        words_per_second: 每秒字数
        min_duration: 最小时长（秒）
        max_duration: 最大时长（秒）
    
    Returns:
        每个场景的时长列表
    """
    durations = []
    
    for scene in script:
        narration = scene.get('narration', '')
        
        if not narration:
            # 如果没有旁白，使用默认时长或剧本中指定的时长
            duration = scene.get('duration', 5.0)
        else:
            # 根据旁白长度计算时长
            duration = calculate_narration_duration(
                narration, 
                words_per_second=words_per_second
            )
            
            # 应用最小/最大限制
            duration = max(min_duration, min(max_duration, duration))
        
        durations.append(duration)
    
    return durations


def update_script_durations(script: List[Dict], 
                            words_per_second: float = 3.5,
                            min_duration: float = 3.0,
                            max_duration: float = 15.0) -> List[Dict]:
    """
    更新剧本中每个场景的 duration 字段
    
    Args:
        script: 剧本列表
        words_per_second: 每秒字数
        min_duration: 最小时长（秒）
        max_duration: 最大时长（秒）
    
    Returns:
        更新后的剧本列表（原地修改并返回）
    """
    durations = calculate_scene_durations(
        script, 
        words_per_second=words_per_second,
        min_duration=min_duration,
        max_duration=max_duration
    )
    
    for i, scene in enumerate(script):
        scene['duration'] = durations[i]
    
    return script


def analyze_script_timing(script: List[Dict]) -> Dict:
    """
    分析剧本的时长信息
    
    Args:
        script: 剧本列表
    
    Returns:
        时长分析结果
    """
    durations = calculate_scene_durations(script)
    
    analysis = {
        'scene_count': len(script),
        'scene_durations': durations,
        'total_duration': sum(durations),
        'avg_duration': sum(durations) / len(durations) if durations else 0,
        'min_duration': min(durations) if durations else 0,
        'max_duration': max(durations) if durations else 0,
        'narration_lengths': [len(s.get('narration', '')) for s in script]
    }
    
    return analysis


if __name__ == "__main__":
    # 测试
    print("=" * 60)
    print("时长计算器测试")
    print("=" * 60)
    
    test_script = [
        {
            "narration": "哈喽大家好！今天带你们探索北京故宫！",
            "visual_query": "Beijing Forbidden City",
        },
        {
            "narration": "故宫，又名紫禁城，是中国明清两代的皇家宫殿，距今已有六百多年的历史。",
            "visual_query": "Forbidden City architecture",
        },
        {
            "narration": "红墙金瓦，气势恢宏。",
            "visual_query": "Red walls and golden tiles",
        },
        {
            "narration": "太和殿是故宫最大的宫殿，也是整个紫禁城的中心建筑，曾经是皇帝举行重大典礼的地方。",
            "visual_query": "Hall of Supreme Harmony",
        },
        {
            "narration": "如果你也想来，记得关注我，我们下期再见！",
            "visual_query": "Waving goodbye",
        }
    ]
    
    print("\n原始剧本：")
    for i, scene in enumerate(test_script, 1):
        narration = scene['narration']
        length = len([c for c in narration if '\u4e00' <= c <= '\u9fff'])
        print(f"  场景 {i}: {narration} ({length}字)")
    
    # 计算时长
    durations = calculate_scene_durations(test_script)
    
    print("\n计算后的时长：")
    for i, duration in enumerate(durations, 1):
        narration = test_script[i-1]['narration']
        length = len([c for c in narration if '\u4e00' <= c <= '\u9fff'])
        print(f"  场景 {i}: {duration}秒 ({length}字)")
    
    # 分析统计
    analysis = analyze_script_timing(test_script)
    print("\n时长分析：")
    print(f"  总场景数: {analysis['scene_count']}")
    print(f"  总时长: {analysis['total_duration']:.1f}秒")
    print(f"  平均时长: {analysis['avg_duration']:.1f}秒")
    print(f"  时长范围: {analysis['min_duration']:.1f}秒 - {analysis['max_duration']:.1f}秒")
    
    # 更新剧本
    updated_script = update_script_durations(test_script.copy())
    print("\n更新后的剧本包含 duration 字段:")
    for i, scene in enumerate(updated_script, 1):
        print(f"  场景 {i}: {scene['duration']}秒")
