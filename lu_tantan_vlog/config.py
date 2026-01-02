"""
配置文件 - 管理本地和远程服务的配置
"""
import os
from dotenv import load_dotenv

# 强制重新加载环境变量，覆盖已存在的变量
load_dotenv(override=True)


class Config:
    """项目配置类"""
    
    # ========== 通义万相 API 配置 ==========
    # 阿里云通义万相 API Key
    TONGYI_API_KEY = os.getenv("TONGYI_API_KEY", "")
    
    # ========== OpenAI API 配置（用于脚本生成）==========
    # OpenAI API Key (用于脚本生成)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # Edge-TTS 配置
    TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-YunxiNeural")  # 男声，可选 zh-CN-XiaoxiaoNeural (女声)
    
    # 视频输出配置
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", "24"))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1080"))
    VIDEO_CODEC = os.getenv("VIDEO_CODEC", "libx264")
    AUDIO_CODEC = os.getenv("AUDIO_CODEC", "aac")
    
    # 文件路径配置
    ASSETS_DIR = os.getenv("ASSETS_DIR", "assets")
    AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
    IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
    OUTPUT_DIR = os.path.join(ASSETS_DIR, "output")
    
    @classmethod
    def ensure_dirs(cls):
        """确保所有必要的目录存在"""
        os.makedirs(cls.AUDIO_DIR, exist_ok=True)
        os.makedirs(cls.IMAGES_DIR, exist_ok=True)
        os.makedirs(cls.OUTPUT_DIR, exist_ok=True)
    
    @classmethod
    def get_status(cls):
        """获取服务状态信息"""
        status = {
            "tongyi_configured": bool(cls.TONGYI_API_KEY),
            "openai_configured": bool(cls.OPENAI_API_KEY),
        }
        return status
    
    @classmethod
    def validate(cls):
        """验证配置是否完整"""
        issues = []
        
        if not cls.TONGYI_API_KEY:
            issues.append("通义万相 API Key 未配置，请在 .env 文件中设置 TONGYI_API_KEY")
        
        if not cls.OPENAI_API_KEY:
            issues.append("OpenAI API Key 未配置（可选，用于脚本生成）")
        
        return issues
