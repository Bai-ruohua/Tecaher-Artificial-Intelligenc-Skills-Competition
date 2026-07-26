# -*- coding: utf-8 -*-
"""
DeepSeek API 统一调用客户端
支持 Chat + Reasoner 双模型，备用API自动切换
"""
from openai import OpenAI
from config import Config


class DeepSeekClient:
    """DeepSeek API客户端封装"""

    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.base_url = Config.DEEPSEEK_BASE_URL
        self.chat_model = Config.DEEPSEEK_MODEL_CHAT
        self.reasoner_model = Config.DEEPSEEK_MODEL_REASONER

        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 备用客户端
        self.alt_client = None
        if Config.ALTERNATE_API_KEY and Config.ALTERNATE_BASE_URL:
            self.alt_client = OpenAI(
                api_key=Config.ALTERNATE_API_KEY,
                base_url=Config.ALTERNATE_BASE_URL
            )

    def _call(self, model, messages, max_tokens=4096, temperature=0.7, stream=False):
        """核心调用方法，自动fallback"""
        clients = [(self.client, model)]
        if self.alt_client:
            clients.append((self.alt_client, Config.ALTERNATE_MODEL))

        for client, m in clients:
            if not client:
                continue
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=stream,
                )
                if stream:
                    return resp
                return resp.choices[0].message.content
            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(f"所有API调用均失败: {last_error}")

    def chat(self, system_prompt, user_message, max_tokens=4096, temperature=0.7):
        """标准Chat对话"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self._call(self.chat_model, messages, max_tokens, temperature)

    def reasoner(self, system_prompt, user_message, max_tokens=8192):
        """DeepSeek Reasoner深度推理"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self._call(self.reasoner_model, messages, max_tokens, temperature=0.1)

    def chat_with_history(self, messages, max_tokens=4096, temperature=0.7):
        """带历史记录的对话"""
        return self._call(self.chat_model, messages, max_tokens, temperature)

    def is_available(self):
        return self.client is not None


# 全局单例
deepseek = DeepSeekClient()
