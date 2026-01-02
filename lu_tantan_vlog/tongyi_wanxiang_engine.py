"""
通义万相视频生成引擎
使用阿里云通义万相 API 生成视频
"""

import os
import time
import json
import requests
from typing import List, Dict, Optional
from http import HTTPStatus
from config import Config

# 尝试导入 dashscope SDK（用于文生视频）
try:
    import dashscope
    from dashscope import VideoSynthesis, ImageSynthesis

    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False
    print("⚠️ dashscope SDK 未安装，文生视频功能将不可用")
    print("   安装命令: pip install dashscope")


class TongyiWanxiangEngine:
    """通义万相视频生成引擎"""

    def __init__(self, api_key: str = None):
        """
        初始化通义万相引擎

        Args:
            api_key: 阿里云通义万相 API Key
        """
        self.api_key = api_key or Config.TONGYI_API_KEY
        # 通义万相 API 端点
        self.image_generation_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
        self.image_to_video_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/image2video/image-to-video"
        self.text_to_video_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2video/text-to-video"
        # 新增：文生视频 API (wan2.6-t2v)
        self.video_synthesis_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
        # 注意：通义万相不提供稳定的语音合成 API，请使用 Edge-TTS (audio_engine.py)

        if not self.api_key:
            raise ValueError(
                "通义万相 API Key 未配置，请在 .env 文件中设置 TONGYI_API_KEY"
            )

        # 配置 dashscope SDK
        if DASHSCOPE_AVAILABLE:
            dashscope.api_key = self.api_key
            dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"

    def generate_image_from_text(
        self, prompt: str, output_path: str = None, return_url: bool = False
    ) -> Optional[str]:
        """
        根据文本描述生成图片

        Args:
            prompt: 图片描述文本
            output_path: 输出文件路径
            return_url: 是否返回 URL 而不是本地路径（用于图生视频）

        Returns:
            生成的图片文件路径或 URL，失败返回 None
        """
        print(f"🎨 开始生成图片: {prompt[:50]}...")

        # 准备请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",  # 启用异步模式
        }

        # 通义万相文生图参数
        data = {
            "model": "wanx-v1",
            "input": {"prompt": prompt},
            "parameters": {"size": "1280*720", "n": 1},  # 16:9 比例，适合视频
        }

        try:
            # 提交生成任务
            response = requests.post(
                self.image_generation_url, headers=headers, json=data, timeout=30
            )

            if response.status_code != 200:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None

            result = response.json()

            # 检查是否有任务ID
            task_id = result.get("output", {}).get("task_id")

            if not task_id:
                print(f"❌ 未获取到任务ID: {result}")
                return None

            print(f"✅ 任务已提交，任务ID: {task_id}")

            # 轮询任务状态
            image_url = self._poll_task_status_for_image(task_id, headers)

            if not image_url:
                return None

            # 如果需要返回 URL（用于图生视频）
            if return_url:
                return image_url

            # 下载图片
            if output_path:
                return self._download_image(image_url, output_path)

            return image_url

        except Exception as e:
            print(f"❌ 图片生成失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _poll_task_status_for_image(
        self, task_id: str, headers: dict, max_wait: int = 120
    ) -> Optional[str]:
        """
        轮询图片生成任务状态

        Args:
            task_id: 任务ID
            headers: 请求头
            max_wait: 最大等待时间（秒）

        Returns:
            图片URL，失败返回 None
        """
        start_time = time.time()

        # 任务查询 URL
        query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(query_url, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"⚠️ 查询任务状态失败: {response.status_code}")
                    time.sleep(3)
                    continue

                result = response.json()
                status = result.get("output", {}).get("task_status", "")

                if status == "SUCCEEDED":
                    results = result.get("output", {}).get("results", [])
                    if results and len(results) > 0:
                        image_url = results[0].get("url", "")
                        if image_url:
                            print(f"✅ 图片生成成功!")
                            return image_url
                    print(f"❌ 任务完成但未获取到图片URL")
                    return None

                elif status == "FAILED":
                    error_msg = result.get("output", {}).get("message", "未知错误")
                    print(f"❌ 图片生成失败: {error_msg}")
                    return None

                elif status in ["PENDING", "RUNNING"]:
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ 图片生成中... ({elapsed}s)", end="\r")
                    time.sleep(3)

                else:
                    print(f"⚠️ 未知状态: {status}")
                    time.sleep(3)

            except Exception as e:
                print(f"⚠️ 查询任务状态异常: {e}")
                time.sleep(3)

        print(f"\n❌ 任务超时（超过 {max_wait} 秒）")
        return None

    def _download_image(self, image_url: str, output_path: str) -> Optional[str]:
        """
        下载图片文件

        Args:
            image_url: 图片URL
            output_path: 输出文件路径

        Returns:
            下载的文件路径，失败返回 None
        """
        try:
            print(f"📥 正在下载图片...")

            response = requests.get(image_url, stream=True, timeout=60)

            if response.status_code != 200:
                print(f"❌ 下载失败: {response.status_code}")
                return None

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 写入文件
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✅ 图片已保存: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 下载图片失败: {e}")
            return None

    def _download_video(self, video_url: str, output_path: str) -> Optional[str]:
        """
        下载视频文件

        Args:
            video_url: 视频URL
            output_path: 输出文件路径

        Returns:
            下载的文件路径，失败返回 None
        """
        try:
            print(f"📥 正在下载视频...")

            response = requests.get(video_url, stream=True, timeout=60)

            if response.status_code != 200:
                print(f"❌ 下载失败: {response.status_code}")
                return None

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 写入文件
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✅ 视频已保存: {output_path}")
            return output_path

        except Exception as e:
            print(f"❌ 下载视频失败: {e}")
            return None

    def generate_images_for_script(
        self, script: List[Dict], output_dir: str = None
    ) -> tuple[List[str], List[str]]:
        """
        为脚本中的每个场景生成图片

        Args:
            script: 脚本列表，每个元素包含 narration, visual_query, duration
            output_dir: 输出目录

        Returns:
            (图片文件路径列表, 图片 URL 列表)
        """
        if not output_dir:
            output_dir = Config.IMAGES_DIR

        os.makedirs(output_dir, exist_ok=True)
        image_paths = []
        image_urls = []

        for i, scene in enumerate(script):
            print(f"\n🎨 生成场景 {i+1}/{len(script)}")

            # 使用 visual_query 作为提示词
            prompt = scene.get("visual_query", scene.get("narration", ""))

            output_path = os.path.join(output_dir, f"scene_{i}.jpg")

            # 先获取图片 URL
            image_url = self.generate_image_from_text(
                prompt=prompt, output_path=None, return_url=True
            )

            if image_url:
                image_urls.append(image_url)
                # 下载图片到本地
                image_path = self._download_image(image_url, output_path)
                if image_path and os.path.exists(image_path):
                    image_paths.append(image_path)
                    print(f"✅ 场景 {i+1} 生成成功")
                else:
                    print(f"❌ 场景 {i+1} 下载失败")
                    image_paths.append(None)
            else:
                print(f"❌ 场景 {i+1} 生成失败")
                image_paths.append(None)
                image_urls.append(None)

        return image_paths, image_urls

    def generate_video_from_text_direct(
        self, prompt: str, output_path: str = None, size: str = "1920*1080"
    ) -> Optional[str]:
        """
        直接文生视频 API (wan2.2-t2v-plus)

        使用阿里云通义万相 2.2 文生视频模型直接从文本生成视频
        需要安装 dashscope SDK: pip install dashscope

        Args:
            prompt: 视频描述文本
            output_path: 输出视频路径
            size: 视频尺寸，支持的尺寸：
                  - "1920*1080" (横屏 16:9, 推荐)
                  - "1080*1920" (竖屏 9:16, 抖音/快手)
                  - "1440*1440" (正方形)
                  - "1632*1248"
                  - "1248*1632"
                  - "832*480" (横屏 16:9 小尺寸)
                  - "480*832" (竖屏 9:16 小尺寸)
                  - "624*624" (正方形小尺寸)

        注意：wan2.2-t2v-plus 不支持 duration, audio, shot_type 等参数

        Returns:
            生成的视频文件路径，失败返回 None
        """
        print(f"🎬 开始直接文生视频 (wan2.2-t2v-plus): {prompt[:50]}...")

        if not DASHSCOPE_AVAILABLE:
            print("❌ dashscope SDK 未安装，无法使用文生视频功能")
            print("   安装命令: pip install dashscope")
            return None

        try:
            # 使用 dashscope SDK 异步调用
            print(f"   参数: size={size}")
            rsp = VideoSynthesis.async_call(
                model="wan2.2-t2v-plus", prompt=prompt, size=size
            )

            if rsp.status_code != HTTPStatus.OK:
                print(f"❌ 文生视频请求失败:")
                print(f"   状态码: {rsp.status_code}")
                print(f"   错误码: {rsp.code}")
                print(f"   错误信息: {rsp.message}")
                return None

            task_id = rsp.output.task_id
            print(f"✅ 任务已提交，任务ID: {task_id}")

            # 轮询任务状态
            print(f"⏳ 等待视频生成...")
            max_wait = 300
            start_time = time.time()

            while time.time() - start_time < max_wait:
                result = VideoSynthesis.fetch(task_id)
                status = result.output.task_status

                if status == "SUCCEEDED":
                    video_url = result.output.video_url
                    print(f"\n✅ 视频生成成功!")

                    # 下载视频
                    if output_path:
                        return self._download_video(video_url, output_path)

                    return video_url

                elif status == "FAILED":
                    print(f"\n❌ 视频生成失败")
                    if hasattr(result.output, "message"):
                        print(f"   错误信息: {result.output.message}")
                    return None

                else:
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ 状态: {status}, 已等待 {elapsed}秒...", end="\r")
                    time.sleep(10)

            print(f"\n❌ 任务超时（超过 {max_wait} 秒）")
            return None

        except Exception as e:
            print(f"❌ 直接文生视频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def generate_video_from_text(
        self, prompt: str, output_path: str = None, duration: int = 5
    ) -> Optional[str]:
        """
        文生视频（通过文生图 + 图生视频实现，兼容旧版本）

        注意：建议使用 generate_video_from_text_direct() 方法，
        该方法使用最新的 wan2.6-t2v 模型直接生成视频。

        Args:
            prompt: 视频描述文本
            output_path: 输出视频路径
            duration: 视频时长（建议5-6秒）

        Returns:
            生成的视频文件路径，失败返回 None
        """
        print(f"🎬 开始文生视频（文生图→图生视频）: {prompt[:50]}...")

        try:
            # 步骤 1: 先生成图片
            import tempfile

            temp_image_path = tempfile.NamedTemporaryFile(
                suffix=".jpg", delete=False
            ).name

            print("   步骤 1/2: 生成图片...")
            image_path = self.generate_image_from_text(prompt, temp_image_path)

            if not image_path or not os.path.exists(image_path):
                print(f"❌ 图片生成失败")
                return None

            # 步骤 2: 将图片转为视频
            print("   步骤 2/2: 图片转视频...")
            video_path = self.generate_video_from_image(
                image_path=image_path, output_path=output_path, duration=duration
            )

            # 清理临时图片
            try:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
            except:
                pass

            return video_path

        except Exception as e:
            print(f"❌ 文生视频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def generate_video_from_image_direct(
        self,
        image_path: str = None,
        image_url: str = None,
        prompt: str = "",
        output_path: str = None,
        duration: int = 6,
    ) -> Optional[str]:
        """
        使用通义万相 wan2.2-i2v-plus 图生视频功能（支持 prompt 引导）

        Args:
            image_path: 输入图片路径（本地文件）
            image_url: 图片 URL（优先使用）
            prompt: 视频生成引导词（可选，描述希望图片如何运动）
            output_path: 输出视频路径
            duration: 视频时长（6秒，固定值）

        Returns:
            生成的视频文件路径，失败返回 None
        """
        print(
            f"🎬 开始图生视频 (wan2.2-i2v-plus): {image_path if not image_url else image_url}"
        )
        if prompt:
            print(f"   引导词: {prompt}")

        try:
            # 处理图片 URL
            if not image_url:
                if not image_path:
                    print(f"❌ 必须提供 image_path 或 image_url")
                    return None

                # 检查图片路径是否是 HTTP URL
                if image_path.startswith("http://") or image_path.startswith(
                    "https://"
                ):
                    image_url = image_path
                else:
                    # 本地文件需要 base64 编码
                    import base64

                    if not os.path.exists(image_path):
                        print(f"❌ 图片文件不存在: {image_path}")
                        return None

                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    image_url = f"data:image/jpeg;base64,{image_data}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }

            # 构建请求数据
            input_data = {"img_url": image_url}
            if prompt:
                input_data["prompt"] = prompt

            data = {"model": "wan2.2-i2v-plus", "input": input_data, "parameters": {}}

            # 提交任务
            response = requests.post(
                self.image_to_video_url, headers=headers, json=data, timeout=30
            )

            if response.status_code != 200:
                print(f"❌ 图生视频请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None

            result = response.json()
            task_id = result.get("output", {}).get("task_id")

            if not task_id:
                print(f"❌ 未获取到任务ID: {result}")
                return None

            print(f"✅ 任务已提交，任务ID: {task_id}")

            # 轮询任务状态
            video_url = self._poll_task_status_for_video(task_id, headers)

            if not video_url:
                return None

            # 下载视频
            if output_path:
                return self._download_video(video_url, output_path)

            return video_url

        except Exception as e:
            print(f"❌ 图生视频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def generate_video_from_image(
        self,
        image_path: str,
        output_path: str = None,
        duration: int = 5,
        image_url: str = None,
    ) -> Optional[str]:
        """
        使用通义万相 wanx-v1 图生视频功能（兼容旧版本）

        Args:
            image_path: 输入图片路径（本地文件）
            output_path: 输出视频路径
            duration: 视频时长（最长15秒）
            image_url: 图片的 URL（如果提供，将优先使用 URL）

        Returns:
            生成的视频文件路径，失败返回 None
        """
        print(
            f"🎬 开始图生视频 (wanx-v1): {image_path if not image_url else image_url}"
        )

        try:
            # 如果没有提供 URL，需要使用本地图片路径（通过文件上传或 base64）
            if not image_url:
                # 检查图片路径是否是 HTTP URL
                if image_path.startswith("http://") or image_path.startswith(
                    "https://"
                ):
                    image_url = image_path
                else:
                    # 本地文件需要 base64 编码
                    import base64

                    if not os.path.exists(image_path):
                        print(f"❌ 图片文件不存在: {image_path}")
                        return None

                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode("utf-8")
                    image_url = f"data:image/jpeg;base64,{image_data}"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            }

            data = {
                "model": "wanx-v1",
                "input": {"image_url": image_url},
                "parameters": {"duration": min(duration, 15)},  # 最长15秒
            }

            # 提交任务
            response = requests.post(
                self.image_to_video_url, headers=headers, json=data, timeout=30
            )

            if response.status_code != 200:
                print(f"❌ 图生视频请求失败: {response.status_code}")
                print(f"响应: {response.text}")
                return None

            result = response.json()
            task_id = result.get("output", {}).get("task_id")

            if not task_id:
                print(f"❌ 未获取到任务ID: {result}")
                return None

            print(f"✅ 任务已提交，任务ID: {task_id}")

            # 轮询任务状态
            video_url = self._poll_task_status_for_video(task_id, headers)

            if not video_url:
                return None

            # 下载视频
            if output_path:
                return self._download_video(video_url, output_path)

            return video_url

        except Exception as e:
            print(f"❌ 图生视频失败: {e}")
            import traceback

            traceback.print_exc()
            return None

    def _poll_task_status_for_video(
        self, task_id: str, headers: dict, max_wait: int = 300
    ) -> Optional[str]:
        """
        轮询视频生成任务状态

        Args:
            task_id: 任务ID
            headers: 请求头
            max_wait: 最大等待时间（秒）

        Returns:
            视频URL，失败返回 None
        """
        start_time = time.time()
        query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(query_url, headers=headers, timeout=10)

                if response.status_code != 200:
                    print(f"⚠️ 查询任务状态失败: {response.status_code}")
                    time.sleep(5)
                    continue

                result = response.json()
                status = result.get("output", {}).get("task_status", "")

                if status == "SUCCEEDED":
                    video_url = result.get("output", {}).get("video_url", "")
                    if video_url:
                        print(f"✅ 视频生成成功!")
                        return video_url
                    print(f"❌ 任务完成但未获取到视频URL")
                    return None

                elif status == "FAILED":
                    error_msg = result.get("output", {}).get("message", "未知错误")
                    print(f"❌ 视频生成失败: {error_msg}")
                    return None

                elif status in ["PENDING", "RUNNING"]:
                    elapsed = int(time.time() - start_time)
                    print(f"⏳ 视频生成中... ({elapsed}s)", end="\r")
                    time.sleep(10)

                else:
                    print(f"⚠️ 未知状态: {status}")
                    time.sleep(5)

            except Exception as e:
                print(f"⚠️ 查询任务状态异常: {e}")
                time.sleep(5)

        print(f"\n❌ 任务超时（超过 {max_wait} 秒）")
        return None

    def create_video_from_images(
        self, image_paths: List[str], script: List[Dict], output_path: str
    ) -> bool:
        """
        将图片序列转换为视频

        Args:
            image_paths: 图片文件路径列表
            script: 脚本信息（用于获取每个场景的时长）
            output_path: 输出视频路径

        Returns:
            是否成功
        """
        try:
            from moviepy.editor import ImageClip, concatenate_videoclips

            print(f"\n🎬 正在将 {len(image_paths)} 张图片转换为视频...")

            # 过滤掉 None 和不存在的文件
            valid_images = [
                (img, script[i])
                for i, img in enumerate(image_paths)
                if img and os.path.exists(img) and i < len(script)
            ]

            if not valid_images:
                print("❌ 没有有效的图片可转换")
                return False

            # 创建视频片段
            clips = []
            for img_path, scene in valid_images:
                try:
                    duration = scene.get("duration", 5)
                    clip = ImageClip(img_path, duration=duration)
                    clips.append(clip)
                except Exception as e:
                    print(f"⚠️ 加载图片失败: {img_path}, 错误: {e}")

            if not clips:
                print("❌ 无法加载任何图片")
                return False

            # 拼接视频
            final_clip = concatenate_videoclips(clips, method="compose")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 写入文件
            print(f"💾 正在保存拼接后的视频到: {output_path}")
            final_clip.write_videofile(
                output_path,
                codec=Config.VIDEO_CODEC,
                fps=Config.VIDEO_FPS,
                audio=False,  # 暂时不包含音频
                logger=None,  # 禁用进度条避免卡顿
                threads=4,
                preset='medium',
                verbose=False
            )

            # 清理资源（先关闭合成视频，再关闭源片段）
            print("🧹 清理资源...")
            final_clip.close()
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass

            print(f"✅ 视频创建完成: {output_path}")
            return True

        except Exception as e:
            print(f"❌ 视频创建失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def generate_videos_from_images_direct(
        self,
        image_paths: List[str],
        script: List[Dict],
        output_dir: str = None,
        image_urls: List[str] = None,
        use_prompt: bool = True,
    ) -> List[str]:
        """
        使用通义万相 wan2.2-i2v-plus 为每张图片生成视频（支持 prompt 引导）
        
        ⚠️ 重要：确保所有场景都成功生成视频，否则会导致音视频不同步！

        Args:
            image_paths: 图片文件路径列表
            script: 脚本信息（用于获取每个场景的时长和prompt）
            output_dir: 输出目录
            image_urls: 图片 URL 列表（优先使用 URL）
            use_prompt: 是否使用 narration 作为视频引导词

        Returns:
            生成的视频文件路径列表（失败的场景会被重试，如果仍失败则抛出异常）
        """
        if not output_dir:
            output_dir = Config.IMAGES_DIR

        os.makedirs(output_dir, exist_ok=True)
        video_paths = []
        failed_scenes = []
        
        # 🆕 验证输入：确保图片数量和脚本数量一致
        if len(image_paths) != len(script):
            error_msg = f"❌ 错误：图片数量 ({len(image_paths)}) 与脚本数量 ({len(script)}) 不一致！"
            print(error_msg)
            raise Exception(error_msg)

        for i, image_path in enumerate(image_paths):
            if not image_path or not os.path.exists(image_path):
                print(f"⚠️ 图片 {i+1} 不存在或路径无效: {image_path}")
                failed_scenes.append(i+1)
                video_paths.append(None)
                continue

            print(f"\n🎬 将图片 {i+1}/{len(image_paths)} 转换为视频 (wan2.2-i2v-plus)")

            output_path = os.path.join(output_dir, f"scene_{i}.mp4")

            # 优先使用 URL
            image_url = image_urls[i] if image_urls and i < len(image_urls) else None

            # 获取 prompt（使用 narration 作为运动引导）
            prompt = ""
            if use_prompt and i < len(script):
                prompt = script[i].get("narration", "")

            # 🆕 尝试生成视频（增加重试次数到3次，每次间隔更长）
            video_path = None
            max_retries = 3
            
            for attempt in range(max_retries):
                if attempt > 0:
                    wait_time = attempt * 5  # 递增等待时间：5秒、10秒
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    print(f"🔄 重试场景 {i+1} (第 {attempt+1}/{max_retries} 次尝试)...")
                
                video_path = self.generate_video_from_image_direct(
                    image_path=image_path,
                    image_url=image_url,
                    prompt=prompt,
                    output_path=output_path,
                )
                
                if video_path and os.path.exists(video_path):
                    # 🆕 验证生成的视频文件大小（至少应该有100KB）
                    file_size = os.path.getsize(video_path) / 1024  # KB
                    if file_size < 100:
                        print(f"⚠️ 视频文件太小 ({file_size:.1f}KB)，可能生成失败，继续重试...")
                        continue
                    break

            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
                print(f"✅ 场景 {i+1} 视频生成成功 (大小: {os.path.getsize(video_path)/1024:.1f}KB)")
            else:
                print(f"❌ 场景 {i+1} 视频生成失败（已重试 {max_retries} 次）")
                failed_scenes.append(i+1)
                video_paths.append(None)

        # 🆕 如果有场景失败，给出更详细的错误信息和建议
        if failed_scenes:
            error_msg = (
                f"❌ 严重错误：{len(failed_scenes)} 个场景生成失败！\n"
                f"   失败场景编号: {failed_scenes}\n"
                f"   这将导致音视频严重不同步！\n"
                f"   建议：\n"
                f"   1. 检查通义万相 API 配额是否充足\n"
                f"   2. 检查网络连接是否稳定\n"
                f"   3. 检查图片质量是否符合要求\n"
                f"   4. 尝试减少场景数量后重新生成"
            )
            print(f"\n{error_msg}")
            raise Exception(error_msg)

        print(f"\n✅ 所有 {len(video_paths)} 个场景视频生成成功！")
        return video_paths

    def generate_videos_from_images(
        self,
        image_paths: List[str],
        script: List[Dict],
        output_dir: str = None,
        image_urls: List[str] = None,
    ) -> List[str]:
        """
        使用通义万相 wanx-v1 图生视频功能为每张图片生成视频（兼容旧版本）

        Args:
            image_paths: 图片文件路径列表
            script: 脚本信息（用于获取每个场景的时长）
            output_dir: 输出目录
            image_urls: 图片 URL 列表（优先使用 URL，避免 base64 编码问题）

        Returns:
            生成的视频文件路径列表
        """
        if not output_dir:
            output_dir = Config.IMAGES_DIR

        os.makedirs(output_dir, exist_ok=True)
        video_paths = []

        for i, image_path in enumerate(image_paths):
            if not image_path:
                print(f"⚠️ 图片 {i} 不存在，跳过")
                video_paths.append(None)
                continue

            print(f"\n🎬 将图片 {i+1}/{len(image_paths)} 转换为视频 (wanx-v1)")

            duration = script[i].get("duration", 5) if i < len(script) else 5
            output_path = os.path.join(output_dir, f"scene_{i}.mp4")

            # 优先使用 URL，避免 base64 编码的大小限制
            image_url = image_urls[i] if image_urls and i < len(image_urls) else None

            # 使用图生视频功能
            video_path = self.generate_video_from_image(
                image_path=image_path,
                output_path=output_path,
                duration=duration,
                image_url=image_url,
            )

            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
                print(f"✅ 场景 {i+1} 视频生成成功")
            else:
                print(f"❌ 场景 {i+1} 视频生成失败")
                video_paths.append(None)

        return video_paths

    def generate_videos_from_text_direct(
        self, script: List[Dict], output_dir: str = None, size: str = "1920*1080"
    ) -> List[str]:
        """
        直接从脚本文本生成视频（使用 wan2.2-t2v-plus 模型）
        
        ⚠️ 重要：确保所有场景都成功生成视频，否则会导致音视频不同步！

        Args:
            script: 脚本列表，每个元素包含 narration, visual_query, duration
            output_dir: 输出目录
            size: 视频尺寸

        Returns:
            生成的视频文件路径列表（失败的场景会被重试，如果仍失败则抛出异常）
        """
        if not output_dir:
            output_dir = Config.IMAGES_DIR

        os.makedirs(output_dir, exist_ok=True)
        video_paths = []
        failed_scenes = []

        for i, scene in enumerate(script):
            print(f"\n🎬 生成场景 {i+1}/{len(script)} 的视频 (wan2.2-t2v-plus)")

            # 使用 visual_query 作为提示词
            prompt = scene.get("visual_query", scene.get("narration", ""))
            output_path = os.path.join(output_dir, f"scene_{i}.mp4")

            # 🆕 尝试生成视频（增加重试次数到3次，每次间隔更长）
            video_path = None
            max_retries = 3
            
            for attempt in range(max_retries):
                if attempt > 0:
                    wait_time = attempt * 5  # 递增等待时间：5秒、10秒
                    print(f"⏳ 等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    print(f"🔄 重试场景 {i+1} (第 {attempt+1}/{max_retries} 次尝试)...")
                
                video_path = self.generate_video_from_text_direct(
                    prompt=prompt, output_path=output_path, size=size
                )
                
                if video_path and os.path.exists(video_path):
                    # 🆕 验证生成的视频文件大小（至少应该有100KB）
                    file_size = os.path.getsize(video_path) / 1024  # KB
                    if file_size < 100:
                        print(f"⚠️ 视频文件太小 ({file_size:.1f}KB)，可能生成失败，继续重试...")
                        continue
                    break

            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
                print(f"✅ 场景 {i+1} 视频生成成功 (大小: {os.path.getsize(video_path)/1024:.1f}KB)")
            else:
                print(f"❌ 场景 {i+1} 视频生成失败（已重试 {max_retries} 次）")
                failed_scenes.append(i+1)
                video_paths.append(None)

        # 🆕 如果有场景失败，给出更详细的错误信息和建议
        if failed_scenes:
            error_msg = (
                f"❌ 严重错误：{len(failed_scenes)} 个场景生成失败！\n"
                f"   失败场景编号: {failed_scenes}\n"
                f"   这将导致音视频严重不同步！\n"
                f"   建议：\n"
                f"   1. 检查通义万相 API 配额是否充足\n"
                f"   2. 检查网络连接是否稳定\n"
                f"   3. 尝试简化 visual_query 提示词\n"
                f"   4. 尝试减少场景数量后重新生成"
            )
            print(f"\n{error_msg}")
            raise Exception(error_msg)

        print(f"\n✅ 所有 {len(video_paths)} 个场景视频生成成功！")
        return video_paths

    def generate_videos_from_text(
        self, script: List[Dict], output_dir: str = None
    ) -> List[str]:
        """
        直接从脚本文本生成视频（文生视频模式，兼容旧版本）

        Args:
            script: 脚本列表，每个元素包含 narration, visual_query, duration
            output_dir: 输出目录

        Returns:
            生成的视频文件路径列表
        """
        if not output_dir:
            output_dir = Config.IMAGES_DIR

        os.makedirs(output_dir, exist_ok=True)
        video_paths = []

        for i, scene in enumerate(script):
            print(f"\n🎬 生成场景 {i+1}/{len(script)} 的视频")

            # 使用 visual_query 作为提示词
            prompt = scene.get("visual_query", scene.get("narration", ""))
            duration = scene.get("duration", 5)
            output_path = os.path.join(output_dir, f"scene_{i}.mp4")

            # 使用文生视频功能
            video_path = self.generate_video_from_text(
                prompt=prompt, output_path=output_path, duration=duration
            )

            if video_path and os.path.exists(video_path):
                video_paths.append(video_path)
                print(f"✅ 场景 {i+1} 视频生成成功")
            else:
                print(f"❌ 场景 {i+1} 视频生成失败")
                video_paths.append(None)

        return video_paths

    # 语音合成功能已移除
    # 通义万相不提供稳定的语音合成 API
    # 请使用 audio_engine.py 中的 Edge-TTS（免费且稳定）

    def stitch_images_to_video(
        self, image_paths: List[str], output_path: str, script: List[Dict] = None
    ) -> bool:
        """
        将图片拼接成视频（别名方法）
        """
        return self.create_video_from_images(image_paths, script or [], output_path)

    def stitch_videos(
        self,
        video_paths: List[str],
        output_path: str,
        script: List[Dict] = None,
        target_durations: List[float] = None,
        enable_transitions: bool = True,
        transition_duration: float = 0.5,
    ) -> bool:
        """
        拼接多个视频片段，支持延长视频以适应音频

        Args:
            video_paths: 视频文件路径列表
            output_path: 输出文件路径
            script: 脚本信息（用于添加音频）
            target_durations: 目标时长列表（用于延长视频以适应音频）
            enable_transitions: 是否启用转场效果
            transition_duration: 转场时长（秒）

        Returns:
            是否成功
        """
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips

            print(f"\n🔗 正在拼接 {len(video_paths)} 个视频片段...")

            # 过滤掉 None 和不存在的文件
            valid_paths = [p for p in video_paths if p and os.path.exists(p)]

            if not valid_paths:
                print("❌ 没有有效的视频片段可拼接")
                return False

            # 加载视频片段，并根据 target_durations 延长
            clips = []
            for i, path in enumerate(valid_paths):
                try:
                    clip = VideoFileClip(path)

                    # 如果提供了目标时长，延长视频
                    if target_durations and i < len(target_durations):
                        target_dur = target_durations[i]
                        actual_dur = clip.duration

                        if target_dur > actual_dur * 1.05:  # 需要延长超过5%
                            # 使用慢动作的方式延长视频（更自然流畅）
                            print(
                                f"🔧 延长场景 {i+1}: {actual_dur:.2f}秒 → {target_dur:.2f}秒"
                            )

                            # 计算速度因子（<1 表示减速）
                            speed_factor = actual_dur / target_dur
                            
                            # 限制速度因子范围：0.5-0.9 之间（不要太慢）
                            # 如果需要延长太多，就用混合方案
                            if speed_factor < 0.5:
                                # 方案：慢动作到 0.5x + 冻结帧
                                slow_duration = actual_dur / 0.5  # 减速到 0.5x
                                remaining_duration = target_dur - slow_duration
                                
                                # 减速视频
                                slow_clip = clip.speedx(0.5)
                                
                                # 冻结最后一帧
                                from moviepy.editor import ImageClip, concatenate_videoclips as concat_clips
                                last_frame = clip.get_frame(clip.duration - 0.1)
                                freeze_clip = ImageClip(last_frame, duration=remaining_duration)
                                
                                # 拼接
                                extended_clip = concat_clips([slow_clip, freeze_clip], method="compose")
                                clips.append(extended_clip)
                                
                                print(f"   方法: 慢动作 {slow_duration:.2f}秒 (0.5x) + 冻结帧 {remaining_duration:.2f}秒")
                            else:
                                # 方案：纯慢动作（自然流畅）
                                extended_clip = clip.speedx(speed_factor)
                                clips.append(extended_clip)
                                
                                print(f"   方法: 慢动作 {speed_factor:.2f}x (更流畅自然)")
                        else:
                            clips.append(clip)
                    else:
                        clips.append(clip)

                except Exception as e:
                    print(f"⚠️ 加载视频失败: {path}, 错误: {e}")

            if not clips:
                print("❌ 无法加载任何视频片段")
                return False

            # 🆕 添加转场效果（可选）
            if enable_transitions:
                print(f"🎬 添加转场效果（{transition_duration}秒）...")
                clips_with_transitions = []
                
                for i, clip in enumerate(clips):
                    if i == 0:
                        # 第一个片段：淡入效果
                        clips_with_transitions.append(clip.fadein(transition_duration))
                    elif i == len(clips) - 1:
                        # 最后一个片段：淡出效果
                        clips_with_transitions.append(clip.fadeout(transition_duration))
                    else:
                        # 中间片段：保持原样（交叉淡化在拼接时处理）
                        clips_with_transitions.append(clip)
                
                # 拼接视频（使用 method="compose" 支持淡化效果）
                print("🔗 开始拼接视频片段（含转场）...")
                overlap = min(0.3, transition_duration * 0.6)  # 重叠时长为转场的60%
                final_clip = concatenate_videoclips(
                    clips_with_transitions, 
                    method="compose",
                    padding=-overlap  # 负值表示重叠，实现交叉淡化
                )
            else:
                # 直接拼接，无转场效果
                print("🔗 开始拼接视频片段（无转场）...")
                final_clip = concatenate_videoclips(clips, method="compose")

            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 写入文件
            print(f"💾 正在保存视频到: {output_path}")
            print(f"   编码设置: {Config.VIDEO_CODEC}, {Config.VIDEO_FPS}fps")
            
            final_clip.write_videofile(
                output_path,
                codec=Config.VIDEO_CODEC,
                fps=Config.VIDEO_FPS,
                audio_codec=Config.AUDIO_CODEC,
                logger=None,  # 禁用 moviepy 的进度条，避免卡顿
                threads=4,
                preset='medium',
                verbose=False
            )

            # 清理资源（先关闭合成的视频，再关闭源片段）
            print("🧹 清理视频资源...")
            final_clip.close()
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass

            print(f"✅ 视频拼接完成: {output_path}")
            return True

        except Exception as e:
            print(f"❌ 视频拼接失败: {e}")
            import traceback

            traceback.print_exc()
            return False
