import asyncio
from groq import AsyncGroq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger
from core.config import settings


class LLMRouter:
    def __init__(self):
        self._groq: AsyncGroq | None = None

    @property
    def groq(self) -> AsyncGroq:
        if not self._groq:
            if not settings.GROQ_API_KEY:
                raise RuntimeError("GROQ_API_KEY not set. Copy .env.example to .env and add your key.")
            self._groq = AsyncGroq(api_key=settings.GROQ_API_KEY)
        return self._groq

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        model = model or settings.PRIMARY_MODEL
        logger.debug(f"LLM call | model={model} | messages={len(messages)}")
        response = await self.groq.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content
        logger.debug(f"LLM response | tokens={response.usage.total_tokens}")
        return content

    async def fast_chat(self, messages: list[dict], **kwargs) -> str:
        return await self.chat(messages, model=settings.FAST_MODEL, **kwargs)


llm = LLMRouter()
