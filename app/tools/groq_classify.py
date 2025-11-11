import asyncio
from functools import lru_cache

from groq import Groq

from app.configs.logger import get_logger
from app.configs.settings import settings

logger = get_logger(__name__)


@lru_cache()
def load_env_settings():
    with open(settings.GROQ_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as file:
        system_prompt = file.read()
    return settings.GROQ_API_KEY, system_prompt


class GroqClassifier:
    def __init__(self):
        _settings = load_env_settings()
        self.api_key = _settings[0]
        self.system_prompt = _settings[1]

    async def classify(self, text: str) -> str:
        client = Groq(api_key=self.api_key)
        response = await asyncio.to_thread(
            client.chat.completions.create,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": text},
            ],
            model="openai/gpt-oss-20b",
        )
        if response.choices[0].message.content:
            logger.info(
                f"Groq classification response: {response.choices[0].message.content}"
            )
            return response.choices[0].message.content
        return " "


groq_classifier: GroqClassifier | None = None


def get_groq_classifier() -> GroqClassifier:
    """Get singleton GroqClassifier instance."""
    try:
        logger.info("Creating GroqClassifier instance")
        return GroqClassifier()
    except Exception as e:
        logger.error(f"Error creating GroqClassifier instance: {e}")
        return GroqClassifier()  # Fallback to a new instance
