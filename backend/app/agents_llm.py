import re
from openai import OpenAI
from app.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _client


def _sanitize(text: str) -> str:
    """删除 surrogate 字符，避免 Windows UTF-16 环境 json.dumps 报错"""
    if not isinstance(text, str):
        return text
    return re.sub(r'[\ud800-\udfff]', '', text)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
    response_format: dict | None = None,
) -> str:
    """统一 LLM 调用入口：发送 system + user 两条消息，返回生成文本"""
    client = _get_client()

    system_prompt = _sanitize(system_prompt)
    user_prompt = _sanitize(user_prompt)

    kwargs = {
        "model": settings.llm_model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    if response_format:
        kwargs["response_format"] = response_format

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def call_llm_with_messages(
    messages: list[dict],
    temperature: float = 0.3,
    response_format: dict | None = None,
) -> str:
    """多轮对话 LLM 调用：允许传入完整消息历史"""
    client = _get_client()

    sanitized = []
    for msg in messages:
        sanitized.append({
            "role": msg["role"],
            "content": _sanitize(msg.get("content", "")),
        })

    kwargs = {
        "model": settings.llm_model,
        "temperature": temperature,
        "messages": sanitized,
    }
    if response_format:
        kwargs["response_format"] = response_format

    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content
