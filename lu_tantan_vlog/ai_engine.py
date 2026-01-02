import os
import json
from openai import OpenAI
import requests
from dotenv import load_dotenv
from config import Config

load_dotenv()

# 初始化 OpenAI（仅在配置了 API Key 时）
client = None
if Config.OPENAI_API_KEY:
    client = OpenAI(
        api_key=Config.OPENAI_API_KEY,
        base_url=Config.OPENAI_API_BASE
    )


def generate_vlog_script(location, mode, user_photos_descriptions=None, style_name="热情活力"):
    """
    根据地点生成 JSON 格式的分镜脚本。
    目标时长：1分钟 (约 180-220 字)
    
    Args:
        location: 旅行地点
        mode: 模式 ('upload' 或 'guide')
        user_photos_descriptions: 用户照片描述（可选）
        style_name: 剧本风格名称（默认"热情活力"）
    """
    from script_styles import get_style_prompt_addition

    # 如果没有 Key，返回模拟数据用于测试
    if not Config.OPENAI_API_KEY or not client:
        print("⚠️  未配置 OpenAI API Key，使用模拟数据")
        return _get_mock_script(location)

    # 获取风格配置的 prompt 补充
    style_addition = get_style_prompt_addition(style_name)

    prompt = f"""
    你现在是 AI 旅行博主"路探探"，专注于创作有趣、生动的旅行视频。
    请为地点"{location}"生成一个 1 分钟左右的 Vlog 视频脚本。

    模式：{'用户已有照片的回忆 Vlog' if mode == 'upload' else '未去过的种草/攻略 Vlog'}
    {style_addition}

    ## 内容要求：
    1. **场景数量**：5-6 个场景，紧凑精炼
    2. **总时长**：50-70 秒
    3. **叙事结构**：
       - 开场：吸引眼球的开场白（5-8秒）
       - 主体：2-3个特色场景的深度展示（每个10-12秒）
       - 转场：1-2个快节奏的过渡场景（每个5-8秒）
       - 结尾：总结和呼吁关注（5-8秒）

    ## 每个场景必须包含：
    1. **narration** (旁白文本，中文)：
       - 要生动具体，避免泛泛而谈
       - 融入感官描述（视觉、听觉、味觉等）
       - 加入个人感受和故事性
       - 长度：15-35 字为宜
    
    2. **visual_query** (英文视觉生成提示词，极其详细)：
       - **开场和结尾场景规则**：
         * 第1个和最后1个场景：**严禁包含特定人物**（如 vlogger, host, presenter, me, I）
         * 可以有自然的城市人群场景（如 bustling crowd, people walking）
         * 禁用：vlogger, host, presenter, influencer, me, my, I, close-up face
       - **中间场景规则**：
         * 可以自然包含人物元素（如 people walking, tourists visiting, crowd, travelers）
         * 让场景更真实和有生活气息
       - **视觉一致性要求（重要）**：
         * **统一风格**：所有场景使用一致的视觉风格关键词
         * **色调统一**：保持相似的色彩基调（如 warm tones, vibrant colors）
         * **光线连贯**：按时间顺序规划光线（morning light → golden hour → evening glow）
         * **地点连贯**：明确提到同一地点的不同角度/区域
         * **质量一致**：所有场景使用相同的质量描述（cinematic, 4K, professional）
       - **必须极其具体和详细**，包含以下所有要素：
         * 主体对象（景观、建筑、物品）+ **地点名称**
         * 详细视觉特征（颜色、材质、纹理）+ **统一色调**
         * 光线与氛围（时间顺序：morning → afternoon → golden hour → evening）
         * 动作或状态（sunrise, bustling street, serene landscape）
         * 镜头视角（保持风格一致：多用 cinematic wide angle, aerial drone）
         * 画面质量描述（固定：cinematic style, 4K ultra detailed, professional travel photography）
       - 示例：
         * ❌ 开场禁止：\"Vlogger introducing Tokyo street\"
         * ✅ 开场正确：\"Tokyo skyline panorama with iconic tower...\"
         * ✅ 中间场景（可含人群）：\"Busy Shibuya crossing at night with crowds of people crossing, vibrant neon lights reflecting on wet pavement, urban traffic flowing, cinematic wide angle shot, 4K quality, energetic city atmosphere\"
         * ❌ 太泛：\"temple\"
         * ✅ 极好：\"Ancient Japanese temple with vermillion red torii gate, surrounded by blooming pink cherry blossoms in spring, soft morning sunlight filtering through trees, serene atmosphere, drone aerial view, ultra detailed, professional photography\"
         * ✅ 食物场景（必须专业且无人物）：\"Delicious traditional local cuisine beautifully plated on elegant white ceramic dishes, vibrant colorful fresh ingredients glistening with appetizing textures, artistic professional food styling, warm soft natural lighting from side creating depth and highlights, close-up macro shot with shallow depth of field bokeh background, steam rising gently adding atmosphere, food photography masterpiece, restaurant quality presentation, ultra sharp details, mouthwatering appeal, 8K quality, Michelin star level\"
       - 长度：20-40 个英文单词
       - 必须包含：主体 + 细节 + 光线 + 氛围 + 视角 + 质量描述
    
    3. **negative_prompt** (负面提示词，英文)：
       - 描述不希望出现的元素
       - **特别注意：食物场景必须排除人物元素**
         * 食物场景必须包含：people, person, hands, fingers, human, face, body, chopsticks in hand, eating, dirty dishes, table clutter, plastic containers, wilted food, burnt, undercooked
       - 常见负面词：blurry, low quality, distorted, deformed, ugly, amateur, pixelated, grainy, overexposed, underexposed, bad composition, watermark, text, logo
       - 示例：\"blurry, low quality, distorted, bad composition, amateur photography, pixelated, grainy\"
       - 食物场景示例：\"blurry, low quality, unappetizing, messy, bad food presentation, people, person, hands, fingers, chopsticks in hand, eating, dirty dishes, plastic containers, wilted food\"
       - 长度：5-20 个英文单词
    
    4. **duration** (秒数)：
       - 开场/结尾：5-8秒
       - 主场景：10-12秒
       - 过渡场景：5-8秒

    ## 内容深度要求：
    - 突出{location}的**独特性**和**标志性元素**
    - 包含当地的**文化、美食、自然景观、人文特色**
    - 每个场景要有**明确的视觉焦点**
    - 旁白要有**情感和节奏变化**

    ## JSON 格式示例：
    [
        {{
            "narration": "哈喽大家好！今天路探探带你打卡京都最美的樱花季！",
            "visual_query": "Kyoto city skyline panorama with iconic ancient temples and pagodas, surrounded by blooming pink cherry blossoms in full spring glory, golden hour warm lighting creating magical atmosphere, cinematic wide angle aerial shot, professional 4K quality, vibrant colors, peaceful zen ambiance",
            "negative_prompt": "blurry, low quality, people, person, human, face, body, bad lighting, amateur, pixelated, grainy, overexposed",
            "duration": 6
        }},
        {{
            "narration": "清晨的伏见稻荷大社，千本鸟居在阳光下闪着金光。",
            "visual_query": "Fushimi Inari shrine with endless vermillion red torii gates forming a tunnel, morning golden sunlight filtering through creating dramatic shadows and light rays, peaceful zen atmosphere, ultra detailed architecture, cinematic drone aerial view, professional photography, 4K quality",
            "negative_prompt": "blurry, low quality, distorted, bad composition, amateur, dark, underexposed, crowded, messy",
            "duration": 10
        }},
        {{
            "narration": "穿过鸟居，仿佛走进了另一个世界。",
            "visual_query": "Red Japanese torii gate tunnel perspective with visitors walking through, leading into mystical bright light, atmospheric fog creating dreamy ambiance, vermillion gates forming beautiful corridor, people silhouettes adding scale and life, cinematic depth perspective shot, dramatic ethereal lighting, spiritual zen atmosphere, ultra detailed architecture, professional cinematography",
            "negative_prompt": "blurry, low quality, vlogger, host, close-up face, presenter, bad composition, distorted perspective, amateur, pixelated, overexposed",
            "duration": 5
        }},
        {{
            "narration": "中午必须尝尝正宗的京都怀石料理，每一道都是艺术品！",
            "visual_query": "Exquisite Japanese kaiseki cuisine beautifully arranged on traditional handcrafted ceramics, colorful seasonal ingredients including sashimi and vegetables, garnished with edible flowers, soft natural lighting, close-up macro food photography, ultra detailed textures, professional culinary photography, 4K quality",
            "negative_prompt": "blurry, low quality, bad food presentation, messy, unappetizing, dark, amateur photography, distorted colors, people, person, hands, human face, body parts, chopsticks in hand, eating scene, dirty dishes, plastic containers, wilted food, burnt, undercooked",
            "duration": 10
        }}
    ]

    请根据{location}的实际特色，生成符合上述要求的完整脚本。
    记住：visual_query 越具体详细越好，这样才能搜索/生成到真正相关的视觉素材！
    """

    try:
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[{"role": "system", "content": "You are a JSON generator."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        script_data = json.loads(content)
        # 兼容不同的 JSON 返回结构，确保拿到 list
        if isinstance(script_data, dict) and "scenes" in script_data:
            script = script_data["scenes"]
        else:
            script = script_data
        
        # 🆕 后处理1：添加视觉一致性
        script = _add_visual_consistency(script, location)
        
        # 🆕 后处理2：增强食物场景
        script = _enhance_food_scenes(script)
        
        # 🆕 后处理3：过滤开场和结尾的人物关键词
        script = _filter_person_keywords(script)
        
        return script
    except Exception as e:
        print(f"LLM Error: {e}")
        return _get_mock_script(location)


def _add_visual_consistency(script: list, location: str) -> list:
    """
    为所有场景添加视觉一致性关键词，确保风格统一
    
    Args:
        script: 剧本列表
        location: 地点名称
    
    Returns:
        优化后的剧本列表
    """
    if not script:
        return script
    
    # 统一的风格关键词（所有场景共享）
    consistency_keywords = {
        'style': 'cinematic style, professional travel photography, 4K ultra detailed',
        'tone': 'vibrant warm tones, natural color grading, cohesive visual aesthetic',
        'quality': 'high production value, smooth transitions, consistent lighting',
    }
    
    # 时间顺序光线（根据场景位置分配）
    time_progression = [
        'soft morning light, fresh atmosphere',           # 开场
        'bright daylight, clear visibility',              # 早期场景
        'afternoon natural lighting, warm ambiance',      # 中期场景
        'golden hour glow, magical atmosphere',           # 后期场景
        'sunset warm tones, nostalgic mood'               # 结尾
    ]
    
    total_scenes = len(script)
    
    for idx, scene in enumerate(script):
        visual_query = scene.get('visual_query', '')
        
        # 1. 添加地点名称（如果没有）
        if location.lower() not in visual_query.lower():
            visual_query = f"{location} - {visual_query}"
        
        # 2. 添加时间光线
        time_idx = min(idx, len(time_progression) - 1)
        if idx == total_scenes - 1:  # 最后一个场景
            time_idx = len(time_progression) - 1
        time_light = time_progression[time_idx]
        
        # 3. 组合所有一致性关键词
        style_suffix = f", {consistency_keywords['style']}, {consistency_keywords['tone']}, {time_light}"
        
        # 避免重复添加
        if 'cinematic style' not in visual_query:
            visual_query += style_suffix
        
        scene['visual_query'] = visual_query
        
        print(f"✅ 场景 {idx + 1} 已添加视觉一致性关键词 (光线: {time_light.split(',')[0]})")
    
    return script


def _enhance_food_scenes(script: list) -> list:
    """
    自动增强食物场景的提示词质量
    
    Args:
        script: 原始剧本列表
    
    Returns:
        增强后的剧本列表
    """
    # 食物相关关键词（用于识别食物场景）
    food_keywords_cn = ['美食', '食物', '料理', '菜', '吃', '尝', '品尝', '火锅', '小吃', '餐', '味道', '特色菜', '招牌', '名吃']
    food_keywords_en = ['food', 'cuisine', 'dish', 'meal', 'eat', 'taste', 'restaurant', 'culinary', 'delicious', 'gourmet', 'flavor', 'recipe']
    
    # 食物场景必须添加的正面关键词（专业食物摄影级别）
    food_positive_keywords = [
        'beautifully plated on elegant ceramic dishes',
        'vibrant colorful fresh ingredients with glistening textures',
        'artistic professional food styling and composition',
        'warm soft natural side lighting creating depth and highlights',
        'close-up macro food photography with ultra sharp focus',
        'shallow depth of field with creamy bokeh background',
        'steam rising elegantly adding dynamic atmosphere',
        'garnished with fresh herbs and decorative elements',
        'food photography masterpiece with restaurant quality presentation',
        'ultra detailed textures showing moisture and freshness',
        'mouthwatering appetizing appeal',
        'Michelin star level plating',
        'professional culinary magazine quality',
        '8K ultra high resolution',
        'perfect color balance and saturation',
        'artisan crafted appearance'
    ]
    
    # 食物场景必须添加的负面关键词（全面排除人物和低质量元素）
    food_negative_keywords = [
        'people', 'person', 'persons', 'human', 'humans', 'man', 'woman', 'child',
        'hands', 'fingers', 'arms', 'face', 'faces', 'body', 'bodies',
        'hand holding', 'chopsticks in hand', 'fork in hand', 'spoon in hand',
        'eating', 'eating scene', 'dining', 'someone eating',
        'dirty dishes', 'used plates', 'messy table', 'table clutter',
        'plastic containers', 'takeout boxes', 'paper plates', 'disposable',
        'wilted vegetables', 'wilted food', 'rotten', 'spoiled',
        'burnt food', 'overcooked', 'undercooked', 'raw meat', 'frozen food',
        'bad food presentation', 'unappetizing', 'messy plating',
        'blurry food', 'out of focus', 'low quality photography',
        'bad lighting', 'dark shadows', 'overexposed highlights',
        'amateur food photo', 'phone camera quality',
        'watermark', 'text overlay', 'logo'
    ]
    
    for idx, scene in enumerate(script):
        narration = scene.get('narration', '')
        visual_query = scene.get('visual_query', '')
        negative_prompt = scene.get('negative_prompt', '')
        
        # 判断是否为食物场景
        is_food_scene = False
        for keyword in food_keywords_cn:
            if keyword in narration:
                is_food_scene = True
                break
        
        if not is_food_scene:
            for keyword in food_keywords_en:
                if keyword.lower() in visual_query.lower():
                    is_food_scene = True
                    break
        
        if is_food_scene:
            print(f"🍽️ 检测到食物场景 {idx + 1}，正在优化提示词...")
            
            # 增强正面提示词
            enhanced_positive = []
            for keyword in food_positive_keywords:
                if keyword.lower() not in visual_query.lower():
                    enhanced_positive.append(keyword)
            
            if enhanced_positive:
                visual_query += ', ' + ', '.join(enhanced_positive)
                scene['visual_query'] = visual_query
                print(f"   ✅ 添加了 {len(enhanced_positive)} 个专业食物摄影关键词")
            
            # 增强负面提示词
            enhanced_negative = []
            for keyword in food_negative_keywords:
                if keyword.lower() not in negative_prompt.lower():
                    enhanced_negative.append(keyword)
            
            if enhanced_negative:
                negative_prompt += ', ' + ', '.join(enhanced_negative)
                scene['negative_prompt'] = negative_prompt
                print(f"   ✅ 添加了 {len(enhanced_negative)} 个食物场景负面关键词")
    
    return script


def _filter_person_keywords(script: list) -> list:
    """
    过滤开场和结尾场景的人物关键词，保留中间场景
    
    Args:
        script: 原始剧本列表
    
    Returns:
        过滤后的剧本列表
    """
    if not script or len(script) < 2:
        return script
    
    # 需要在开场和结尾过滤的关键词（使用正则表达式模式进行更彻底的清理）
    person_keywords = [
        'vlogger', 'host', 'presenter', 'influencer', 'youtuber',
        'me', 'my', 'I ', ' I,', 'selfie', 'close-up face', 'closeup face', 'portrait',
        'woman', 'man', 'girl', 'boy', 'lady', 'gentleman',
        'smiling at camera', 'looking at camera', 'waving at camera', 'waving',
        'introducing', 'speaking', 'talking', 'saying hello', 'saying goodbye',
        'with smile', 'with smiling face', 'audience', 'viewers', 'camera'
    ]
    
    # 只处理第一个和最后一个场景
    for idx in [0, len(script) - 1]:
        if idx < len(script):
            scene = script[idx]
            visual_query = scene.get('visual_query', '')
            negative_prompt = scene.get('negative_prompt', '')
            
            # 从 visual_query 中移除人物关键词（不区分大小写）
            visual_query_lower = visual_query.lower()
            for keyword in person_keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in visual_query_lower:
                    # 使用原始大小写进行替换
                    import re
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    visual_query = pattern.sub('', visual_query)
            
            # 清理多余的空格、逗号和连续标点
            visual_query = ' '.join(visual_query.split())
            visual_query = visual_query.replace(' ,', ',').replace(',,', ',').replace(', ,', ',')
            visual_query = visual_query.strip(', ')
            
            # 在 negative_prompt 中添加人物关键词
            person_negatives = ['vlogger', 'host', 'presenter', 'influencer', 'close-up face', 'selfie', 'portrait', 'looking at camera', 'smiling at camera']
            for neg in person_negatives:
                if neg not in negative_prompt.lower():
                    negative_prompt += f', {neg}'
            
            # 更新场景
            scene['visual_query'] = visual_query
            scene['negative_prompt'] = negative_prompt
            
            print(f"✅ 已过滤场景 {idx + 1} 的人物关键词")
    
    return script


def search_stock_images(query, count=1):
    """
    使用 Pexels API 搜索图片
    """
    api_key = Config.PEXELS_API_KEY
    if not api_key:
        # 返回占位图
        return [
            "https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"]

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={count}"

    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data['photos']:
                return [p['src']['large'] for p in data['photos']]
    except Exception as e:
        print(f"Pexels Error: {e}")

    return []


def _get_mock_script(location):
    """没有 API Key 时的备用脚本（精简版，5个场景，开场结尾无人物，中间可有人群）"""
    script = [
        {
            "narration": f"哈喽大家好，我是路探探！今天带你们深度探索{location}的魅力！",
            "visual_query": f"Stunning panoramic view of {location} iconic landmarks and cityscape, bright sunny daylight with blue sky, vibrant colorful scenery showcasing destination beauty, cinematic wide angle aerial shot, professional travel photography, 4K quality, welcoming energetic atmosphere",
            "negative_prompt": "blurry, low quality, people, person, human, face, body, vlogger, tourist, bad lighting, amateur, dark, gloomy, pixelated, grainy",
            "duration": 6
        },
        {
            "narration": f"第一站来到{location}最著名的地标，这建筑真的太壮观了！",
            "visual_query": f"Stunning cinematic aerial drone view of famous {location} landmark architecture with magnificent details, dramatic golden hour lighting casting long shadows, epic perspective showcasing scale and grandeur, ultra detailed textures, professional architectural photography, 4K quality, breathtaking composition",
            "negative_prompt": "blurry, low quality, distorted, bad composition, amateur, underexposed, overexposed, pixelated, grainy, boring angle",
            "duration": 12
        },
        {
            "narration": "当地特色美食必须尝一下，这味道绝了！",
            "visual_query": f"Delicious traditional {location} local cuisine beautifully plated on elegant white ceramic dishes, vibrant colorful fresh ingredients glistening with appetizing textures, artistic professional food styling, warm soft natural lighting from side creating depth and highlights, close-up macro shot with shallow depth of field bokeh background, steam rising gently adding atmosphere, food photography masterpiece, restaurant quality presentation, ultra sharp details, mouthwatering appeal, 8K quality, Michelin star level",
            "negative_prompt": "blurry, low quality, unappetizing, messy, bad food presentation, dark, underlit, amateur, distorted colors, grainy, people, person, hands, fingers, human, face, body, chopsticks in hand, eating, dirty dishes, table clutter, plastic containers, takeout boxes, wilted vegetables, burnt food, raw meat, uncooked, frozen food",
            "duration": 12
        },
        {
            "narration": "傍晚时分，这座城市又展现出完全不同的魅力。",
            "visual_query": f"Breathtaking {location} city skyline at golden hour with people enjoying the evening view, warm orange and purple sunset colors painting the sky, city lights beginning to illuminate buildings, visitors and locals creating lively atmosphere, reflections on water or glass surfaces, vibrant energetic ambiance, cinematic wide panoramic shot, professional travel photography, ultra detailed, 4K quality",
            "negative_prompt": "blurry, low quality, bad composition, overexposed sky, underexposed city, amateur, grainy, pixelated, dull colors",
            "duration": 10
        },
        {
            "narration": "如果你也想来，记得关注路探探，我们下期再见！",
            "visual_query": f"Beautiful {location} cityscape panorama at golden hour with stunning architecture and scenic beauty, warm inviting sunset lighting painting sky in orange and pink hues, cinematic wide composition showcasing destination charm, professional travel photography, vibrant welcoming colors, 4K quality, memorable finale atmosphere",
            "negative_prompt": "blurry, low quality, vlogger, host, presenter, close-up face, selfie, portrait, bad lighting, amateur, dark, gloomy, pixelated, grainy",
            "duration": 6
        }
    ]
    
    # 应用后处理函数
    script = _add_visual_consistency(script, location)
    script = _enhance_food_scenes(script)  # 优先增强食物场景
    script = _filter_person_keywords(script)
    return script