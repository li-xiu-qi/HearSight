# -*- coding: utf-8 -*-

from __future__ import annotations

from backend.chat_utils.chat_client import chat_text
from config import get_config


def chat_text_once(prompt: str) -> str:
    config = get_config() 
    openai_config = config.get("chat_server").get("openai")
    api_key = openai_config.get("api_key")
    base_url = openai_config.get("base_url")
    model = openai_config.get("chat_model")
    return chat_text(prompt=prompt, api_key=str(api_key), base_url=str(base_url), model=str(model))
