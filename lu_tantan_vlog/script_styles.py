"""
剧本风格配置模块
定义不同的视频风格及其参数
"""

# 剧本风格定义
SCRIPT_STYLES = {
    "热情活力": {
        "name": "热情活力",
        "icon": "🔥",
        "description": "充满激情和活力，节奏明快，适合年轻观众",
        "tone": "热情洋溢、真实接地气、充满好奇心和感染力",
        "narration_style": "语气活泼、多用感叹句、语速较快",
        "scene_style": "快节奏切换、动感镜头、鲜艳色彩",
        "opening_style": "快速抓住眼球，使用惊叹和疑问",
        "examples": [
            "哈喽大家好！今天路探探带你打卡最美的地方！",
            "太震撼了！没想到这里这么美！",
            "走走走，跟我一起去探索！"
        ],
        "visual_keywords": "vibrant colors, energetic atmosphere, dynamic movement, bright lighting, youthful vibe",
        "pacing": "fast"
    },
    
    "文艺清新": {
        "name": "文艺清新",
        "icon": "🌸",
        "description": "温柔细腻，注重氛围和情感，适合慢节奏欣赏",
        "tone": "温柔细腻、充满诗意、注重情感表达",
        "narration_style": "语气柔和、多用描绘性语言、语速舒缓",
        "scene_style": "柔和过渡、静谧画面、自然色调",
        "opening_style": "以优美的景色或氛围开场",
        "examples": [
            "清晨的第一缕阳光，洒在古老的街道上。",
            "在这里，时间仿佛慢了下来。",
            "风轻轻吹过，带来花的香气。"
        ],
        "visual_keywords": "soft pastel colors, gentle lighting, peaceful atmosphere, natural tones, dreamy ambiance, serene mood",
        "pacing": "slow"
    },
    
    "知识科普": {
        "name": "知识科普",
        "icon": "📚",
        "description": "专业详细，注重信息传达，适合深度了解",
        "tone": "专业准确、知识丰富、条理清晰",
        "narration_style": "语气专业、多用数据和事实、逻辑清晰",
        "scene_style": "稳定镜头、清晰展示、信息丰富",
        "opening_style": "以背景知识或历史开场",
        "examples": [
            "这座建筑建于1420年，距今已有600多年历史。",
            "这里是世界文化遗产，每年吸引上千万游客。",
            "让我们深入了解这个地方的历史文化。"
        ],
        "visual_keywords": "clear details, professional photography, architectural focus, documentary style, informative composition",
        "pacing": "medium"
    },
    
    "美食探店": {
        "name": "美食探店",
        "icon": "🍜",
        "description": "聚焦美食体验，强调味觉和视觉享受",
        "tone": "美味诱人、体验感强、真实推荐",
        "narration_style": "描述味道质感、多用美食词汇、充满食欲",
        "scene_style": "特写美食细节、展现制作过程、诱人色彩",
        "opening_style": "直接展示最吸引人的美食画面",
        "examples": [
            "这家店的招牌菜，一定要尝尝！",
            "看这个汤汁，简直绝了！",
            "第一口就爱上了这个味道！"
        ],
        "visual_keywords": "appetizing food presentation, delicious textures, warm inviting colors, close-up details, steam and freshness",
        "pacing": "medium"
    },
    
    "冒险探索": {
        "name": "冒险探索",
        "icon": "🗺️",
        "description": "强调探索和发现，充满未知和惊喜",
        "tone": "充满好奇、勇于探索、发现惊喜",
        "narration_style": "悬念铺垫、发现式叙述、制造期待",
        "scene_style": "第一视角、未知感、发现瞬间",
        "opening_style": "提出问题或设置悬念",
        "examples": [
            "这条小巷的尽头，隐藏着什么秘密？",
            "跟我一起去探索这个神秘的地方！",
            "没想到在这里发现了宝藏！"
        ],
        "visual_keywords": "mysterious atmosphere, exploration perspective, hidden gems, dramatic reveals, adventure mood",
        "pacing": "varied"
    },
    
    "禅意静心": {
        "name": "禅意静心",
        "icon": "🧘",
        "description": "宁静致远，注重内心感受和精神体验",
        "tone": "宁静平和、内心感悟、精神体验",
        "narration_style": "简洁留白、意境深远、富有哲理",
        "scene_style": "极简构图、留白空间、禅意氛围",
        "opening_style": "以静谧场景或哲理思考开场",
        "examples": [
            "在这里，心会安静下来。",
            "远离喧嚣，找回内心的平静。",
            "简单，却不平凡。"
        ],
        "visual_keywords": "minimalist composition, zen atmosphere, peaceful solitude, natural harmony, spiritual tranquility",
        "pacing": "very_slow"
    },
    
    "奢华精致": {
        "name": "奢华精致",
        "icon": "💎",
        "description": "高端品质，注重细节和品味",
        "tone": "优雅精致、品质至上、细节完美",
        "narration_style": "精炼优雅、强调品质、凸显细节",
        "scene_style": "精美构图、奢华质感、高级氛围",
        "opening_style": "以高级感场景或细节开场",
        "examples": [
            "这里的每一处细节，都值得细细品味。",
            "奢华，不仅是价格，更是品味。",
            "在这里，体验真正的精致生活。"
        ],
        "visual_keywords": "luxury elegance, premium quality, sophisticated details, refined atmosphere, high-end aesthetic",
        "pacing": "slow"
    },
    
    "家庭亲子": {
        "name": "家庭亲子",
        "icon": "👨‍👩‍👧‍👦",
        "description": "温馨有爱，适合全家观看，充满欢乐",
        "tone": "温馨有爱、欢乐有趣、家庭友好",
        "narration_style": "亲切温暖、简单易懂、充满童趣",
        "scene_style": "明亮温馨、有趣互动、安全友好",
        "opening_style": "以温馨或有趣的画面开场",
        "examples": [
            "这里特别适合带孩子来玩！",
            "全家一起度过了美好的一天。",
            "孩子们玩得可开心了！"
        ],
        "visual_keywords": "warm family atmosphere, bright cheerful colors, safe friendly environment, joyful moments",
        "pacing": "medium"
    }
}


def get_style_config(style_name: str) -> dict:
    """
    获取指定风格的配置
    
    Args:
        style_name: 风格名称
    
    Returns:
        风格配置字典
    """
    return SCRIPT_STYLES.get(style_name, SCRIPT_STYLES["热情活力"])


def get_all_styles() -> list:
    """
    获取所有可用风格
    
    Returns:
        风格列表，包含名称和图标
    """
    return [(f"{style_config['icon']} {style_config['name']}", style_config['name']) 
            for style_name, style_config in SCRIPT_STYLES.items()]


def get_style_prompt_addition(style_name: str) -> str:
    """
    根据风格生成额外的 prompt 指令
    
    Args:
        style_name: 风格名称
    
    Returns:
        添加到 prompt 的风格指令
    """
    config = get_style_config(style_name)
    
    prompt_addition = f"""
    
## 风格要求：「{config['name']}」
- **整体基调**：{config['tone']}
- **旁白风格**：{config['narration_style']}
- **场景风格**：{config['scene_style']}
- **开场方式**：{config['opening_style']}
- **节奏控制**：{config['pacing']} paced
- **视觉关键词**：{config['visual_keywords']}

**风格示例旁白**：
{chr(10).join(f'  - "{example}"' for example in config['examples'])}

请确保生成的脚本完全符合「{config['name']}」风格的要求，
旁白的语气、用词和表达方式都要体现这种风格。
视觉描述中要融入对应的氛围关键词。
    """
    
    return prompt_addition


def get_style_description(style_name: str) -> str:
    """
    获取风格描述
    
    Args:
        style_name: 风格名称
    
    Returns:
        风格描述文本
    """
    config = get_style_config(style_name)
    return f"{config['icon']} **{config['name']}**：{config['description']}"


if __name__ == "__main__":
    # 测试
    print("可用的剧本风格：\n")
    for display_name, style_name in get_all_styles():
        print(f"  {display_name}")
        print(f"    {get_style_description(style_name)}")
        print()
