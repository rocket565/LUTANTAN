"""
路探探项目启动脚本
自动检查环境并启动 Streamlit 服务
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def print_banner():
    """打印欢迎信息"""
    banner = """
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║            📷 路探探 (Lu Tantan)                       ║
    ║         AI 旅行博主 Vlog 生成工作台                    ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_env_file():
    """检查 .env 文件是否存在"""
    env_file = Path(".env")
    if not env_file.exists():
        print("警告: .env 配置文件不存在")
        print("建议: 创建 .env 文件并配置必要参数")
        print()

        response = input("是否现在创建默认配置文件? (y/n): ").strip().lower()
        if response == "y":
            create_default_env()
        else:
            print("继续启动... (某些功能可能不可用)")
    else:
        print("配置文件检查通过")


def create_default_env():
    """创建默认的 .env 文件"""
    default_env = """# ========== 工作模式配置 ==========
# 工作模式: remote (使用远程服务) / local (本地生成) / hybrid (混合模式)
WORK_MODE=remote

# ========== 远程服务配置 ==========
# 是否启用远程服务
REMOTE_SERVICE_ENABLED=true

# 远程服务地址 (通过 SSH 隧道访问)
# SSH 命令: ssh -o ServerAliveInterval=60 -CNg -L 4097:127.0.0.1:6006 root@connect.westd.seetacloud.com -p 19130
REMOTE_API_BASE_URL=http://127.0.0.1:4097

# 远程服务超时时间（秒）
REMOTE_API_TIMEOUT=300

# ========== 本地服务配置 ==========
# OpenAI API Key (用于本地脚本生成，remote 模式可选)
OPENAI_API_KEY=

# OpenAI 模型选择
OPENAI_MODEL=gpt-4o

# Pexels API Key (用于本地图片搜索，remote 模式可选)
PEXELS_API_KEY=

# ========== 其他配置 ==========
# TTS 语音选择: zh-CN-YunxiNeural (男声) / zh-CN-XiaoxiaoNeural (女声)
TTS_VOICE=zh-CN-YunxiNeural

# 视频参数
VIDEO_FPS=24
VIDEO_HEIGHT=1080
VIDEO_CODEC=libx264
AUDIO_CODEC=aac
"""

    with open(".env", "w", encoding="utf-8") as f:
        f.write(default_env)

    print("已创建默认配置文件 .env")
    print("请根据需要修改配置后重新启动")


def check_dependencies():
    """快速检查关键依赖"""
    print("\n检查依赖包...")

    required_packages = ["streamlit", "requests", "dotenv"]
    missing = []

    for package in required_packages:
        try:
            if package == "dotenv":
                __import__("dotenv")
            else:
                __import__(package)
            print(f" {package}")
        except ImportError:
            print(f" {package} (未安装)")
            missing.append(package)

    if missing:
        print(f"\n缺少必要依赖: {', '.join(missing)}")
        print("   请运行: pip install -r requirements_full.txt")
        return False

    return True


def start_streamlit():
    """启动 Streamlit 服务"""
    print("\n" + "=" * 60)
    print("启动 Streamlit 服务...")
    print("=" * 60)

    try:
        # 启动 streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", "main.py"]

        # 添加 streamlit 配置参数
        cmd.extend(
            [
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
                "--browser.gatherUsageStats",
                "false",
            ]
        )

        print(f"\n启动命令: {' '.join(cmd)}")
        print("\n服务地址: http://localhost:8501")
        print("按 Ctrl+C 停止服务\n")
        print("=" * 60 + "\n")

        subprocess.run(cmd)

    except KeyboardInterrupt:
        print("\n\n感谢使用路探探！服务已停止。\n")
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("\n尝试手动启动:")
        print("  streamlit run main.py")


def main():
    """主函数"""
    print_banner()

    # 检查配置文件
    check_env_file()

    # 检查依赖
    if not check_dependencies():
        print("\n请先安装依赖后再启动。")
        sys.exit(1)

    # 给用户一点时间查看检查结果
    print("\n准备启动服务...")
    time.sleep(1)

    # 启动服务
    start_streamlit()


if __name__ == "__main__":
    main()
