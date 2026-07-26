# -*- coding: utf-8 -*-
"""
TTS语音合成引擎
支持 GPT-SoVITS 声音克隆 + Edge-TTS 降级方案
"""
import os
import json
import requests
import base64
import hashlib
from config import Config


class TTSEngine:
    """TTS语音合成引擎"""

    def __init__(self):
        self.service_url = Config.TTS_SERVICE_URL
        self.cache_dir = os.path.join(Config.DATA_DIR, "tts_cache")
        os.makedirs(self.cache_dir, exist_ok=True)

    def synthesize(self, text, voice_id="teacher", speed=1.0):
        """
        将文本合成语音
        优先使用GPT-SoVITS服务，失败则降级为Edge-TTS
        """
        cache_key = hashlib.md5(f"{text}_{voice_id}_{speed}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.wav")

        # 缓存命中
        if os.path.exists(cache_path):
            return cache_path

        # 方案A：本地GPT-SoVITS服务
        if self.service_url:
            try:
                result = self._call_gpt_sovits(text, voice_id, speed, cache_path)
                if result:
                    return result
            except Exception:
                pass

        # 方案B：Edge-TTS（无需API Key，无网络依赖轻量方案）
        try:
            return self._call_edge_tts(text, cache_path)
        except Exception:
            pass

        # 方案C：返回空，前端降级为纯文本
        return None

    def _call_gpt_sovits(self, text, voice_id, speed, output_path):
        """调用GPT-SoVITS API"""
        resp = requests.post(
            f"{self.service_url}/tts",
            json={"text": text, "voice": voice_id, "speed": speed},
            timeout=60
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("audio_base64"):
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(data["audio_base64"]))
                return output_path
        return None

    def _call_edge_tts(self, text, output_path):
        """使用Edge-TTS合成（通过本地调用edge-tts命令）"""
        import subprocess
        import tempfile

        # 尝试使用edge-tts命令行
        try:
            subprocess.run(
                ["edge-tts", "--voice", "zh-CN-XiaoxiaoNeural", "--text", text, "--write-media", output_path],
                capture_output=True, timeout=30, check=True
            )
            if os.path.exists(output_path):
                return output_path
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            pass
        return None

    def clone_voice(self, sample_audio_path, voice_name="teacher"):
        """克隆声音（需要GPT-SoVITS服务）"""
        if not self.service_url or not os.path.exists(sample_audio_path):
            return False

        try:
            with open(sample_audio_path, "rb") as f:
                files = {"audio": f}
                data = {"voice_name": voice_name}
                resp = requests.post(f"{self.service_url}/clone_voice", files=files, data=data, timeout=120)
            return resp.status_code == 200
        except Exception:
            return False

    def list_voices(self):
        """列出可用音色"""
        if self.service_url:
            try:
                resp = requests.get(f"{self.service_url}/voices", timeout=10)
                if resp.status_code == 200:
                    return resp.json().get("voices", [])
            except Exception:
                pass
        return ["edge-tts-zh-CN-XiaoxiaoNeural"]


# 全局单例
tts = TTSEngine()
