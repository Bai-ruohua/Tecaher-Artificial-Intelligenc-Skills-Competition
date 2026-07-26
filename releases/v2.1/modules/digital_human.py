# -*- coding: utf-8 -*-
"""
数字人讲解Agent
支持 SadTalker离线预生成 + D-ID API按需生成
"""
import os
import json
import hashlib
import subprocess
import requests
from config import Config
from database import save_digital_human_cache, get_digital_human_cache


class DigitalHumanEngine:
    """数字人生成引擎"""

    def __init__(self):
        self.cache_dir = Config.DIGITAL_HUMAN_CACHE_DIR if Config.DIGITAL_HUMAN_CACHE_ENABLED else None
        self.did_api_key = Config.DID_API_KEY
        self.video_dir = Config.VIDEO_DIR

        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.video_dir, exist_ok=True)

        # SadTalker路径（需要用户自行部署）
        self.sadtalker_path = os.environ.get("SADTALKER_PATH", "")
        self.teacher_photo = os.environ.get("TEACHER_PHOTO", "")

    def generate_video(self, topic_key, answer_text, chapter_id, audio_path=None, method="auto"):
        """
        生成数字人讲解视频

        Args:
            topic_key: 问题/知识点标识（用于缓存）
            answer_text: 讲解文本
            chapter_id: 所属章节
            audio_path: 已生成的音频文件路径
            method: "sadtalker" / "did_api" / "auto"（自动选择）

        Returns:
            {"video_path": str, "audio_path": str, "method": str, "cached": bool}
        """
        # 1. 检查缓存
        if Config.DIGITAL_HUMAN_CACHE_ENABLED:
            cached = get_digital_human_cache(topic_key)
            if cached and cached.get("video_path"):
                video_path = cached["video_path"]
                if os.path.exists(video_path):
                    return {
                        "video_path": video_path,
                        "audio_path": cached.get("audio_path", ""),
                        "method": "cache",
                        "cached": True,
                    }

        # 2. 没有音频时先合成
        if not audio_path:
            from modules.tts_engine import tts
            audio_path = tts.synthesize(answer_text)
            if not audio_path:
                return {"error": "TTS合成失败", "cached": False}

        # 3. 生成数字人视频
        video_path = None
        used_method = "none"

        if method in ("auto", "sadtalker") and self.sadtalker_path and self.teacher_photo:
            try:
                video_path = self._generate_sadtalker(audio_path, topic_key)
                used_method = "sadtalker"
            except Exception as e:
                if method == "sadtalker":
                    return {"error": f"SadTalker生成失败: {str(e)}", "cached": False}

        if not video_path and method in ("auto", "did_api") and self.did_api_key:
            try:
                video_path = self._generate_did_api(answer_text, audio_path, topic_key)
                used_method = "did_api"
            except Exception as e:
                if method == "did_api":
                    return {"error": f"D-ID API失败: {str(e)}", "cached": False}

        if not video_path:
            # 降级：只返回音频，前端显示静态照片+音频
            return {
                "video_path": None,
                "audio_path": audio_path,
                "method": "tts_only",
                "cached": False,
                "fallback": True,
            }

        # 4. 存入缓存
        if Config.DIGITAL_HUMAN_CACHE_ENABLED:
            save_digital_human_cache(
                chapter_id=chapter_id,
                topic_key=topic_key,
                answer_text=answer_text,
                audio_path=audio_path,
                video_path=video_path,
                tts_duration=0,
            )

        return {
            "video_path": video_path,
            "audio_path": audio_path,
            "method": used_method,
            "cached": False,
        }

    def _generate_sadtalker(self, audio_path, topic_key):
        """使用SadTalker生成数字人视频"""
        if not self.sadtalker_path or not self.teacher_photo:
            raise RuntimeError("SadTalker未配置（需要设置SADTALKER_PATH和TEACHER_PHOTO环境变量）")

        output_dir = os.path.join(self.video_dir, topic_key)
        os.makedirs(output_dir, exist_ok=True)

        # SadTalker CLI调用
        # python inference.py --driven_audio <audio> --source_image <photo> --result_dir <output>
        python_bin = os.path.join(self.sadtalker_path, ".venv", "Scripts", "python.exe")
        if not os.path.exists(python_bin):
            python_bin = "python"

        cmd = [
            python_bin,
            os.path.join(self.sadtalker_path, "inference.py"),
            "--driven_audio", audio_path,
            "--source_image", self.teacher_photo,
            "--result_dir", output_dir,
            "--still", "true",
            "--preprocess", "crop",
            "--enhancer", "none",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

        if result.returncode != 0:
            raise RuntimeError(f"SadTalker执行失败: {result.stderr[-500:]}")

        # 查找生成的视频文件
        import glob
        mp4_files = glob.glob(os.path.join(output_dir, "**", "*.mp4"), recursive=True)
        if mp4_files:
            # 移动到统一目录
            import shutil
            dest = os.path.join(self.video_dir, f"{topic_key}.mp4")
            shutil.copy(mp4_files[0], dest)
            return dest

        raise RuntimeError("SadTalker未生成视频文件")

    def _generate_did_api(self, answer_text, audio_path, topic_key):
        """使用D-ID API生成数字人视频"""
        if not self.did_api_key:
            raise RuntimeError("D-ID API Key未配置")

        headers = {
            "Authorization": f"Basic {self.did_api_key}",
            "Content-Type": "application/json",
        }

        # D-ID API: text input mode
        payload = {
            "script": {
                "type": "text",
                "input": answer_text[:500],
                "provider": {"type": "microsoft", "voice_id": "zh-CN-XiaoxiaoNeural"},
            },
            "source_url": self.teacher_photo,
            "config": {"fluent": True, "pad_audio": 0.2},
        }

        # 如果有已合成的TTS音频，使用音频模式
        if audio_path and os.path.exists(audio_path):
            # 上传音频
            upload_url = "https://api.d-id.com/audios"
            with open(audio_path, "rb") as f:
                upload_resp = requests.post(upload_url, headers=headers, files={"audio": f}, timeout=60)
            if upload_resp.status_code == 200:
                audio_url = upload_resp.json().get("url", "")
            else:
                audio_url = None

            if audio_url:
                payload["script"] = {
                    "type": "audio",
                    "audio_url": audio_url,
                }

        # 创建talk任务
        resp = requests.post(Config.DID_API_URL, json=payload, headers=headers, timeout=60)
        if resp.status_code not in (200, 201):
            raise RuntimeError(f"D-ID API创建任务失败: {resp.text}")

        talk_id = resp.json().get("id", "")

        # 轮询等待视频生成
        import time
        for _ in range(30):
            time.sleep(2)
            status_resp = requests.get(f"{Config.DID_API_URL}/{talk_id}", headers=headers, timeout=30)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                if status_data.get("status") == "done":
                    result_url = status_data.get("result_url", "")
                    if result_url:
                        # 下载视频
                        video_resp = requests.get(result_url, timeout=120)
                        if video_resp.status_code == 200:
                            dest = os.path.join(self.video_dir, f"{topic_key}_did.mp4")
                            with open(dest, "wb") as f:
                                f.write(video_resp.content)
                            return dest
                    break
                elif status_data.get("status") == "error":
                    raise RuntimeError(f"D-ID生成失败: {status_data.get('error', 'unknown')}")

        raise RuntimeError("D-ID API生成超时")

    def pre_generate_chapters(self, chapter_id=None):
        """
        预生成章节讲解视频（批量缓存）
        为高频知识点提前生成数字人讲解视频
        """
        from knowledge_base import get_chapter

        tasks = []
        statuses = []

        if chapter_id:
            tasks = [chapter_id]
        else:
            tasks = [f"ch{i:02d}" for i in range(1, 13)]

        for cid in tasks:
            ch = get_chapter(cid)
            if not ch:
                statuses.append({"chapter_id": cid, "status": "not_found"})
                continue

            # 为每个章节生成概览讲解
            topic_key = f"overview_{cid}"
            answer_text = f"""欢迎学习{ch['title']}！
            
本章节的重点内容包括：{'；'.join(ch['key_points'][:5])}。

学习本章之前，你需要掌握：{'；'.join(ch['objectives'][:2])}。

{'；'.join(ch['difficulties'])} 是本章的难点，建议多花时间练习。

让我们开始吧！"""

            statuses.append({
                "chapter_id": cid,
                "topic_key": topic_key,
                "status": "queued",
            })

        return {"total": len(tasks), "details": statuses}

    def is_configured(self):
        """检查数字人生成是否已配置"""
        return bool(self.sadtalker_path or self.did_api_key)


# 全局单例
digital_human = DigitalHumanEngine()
