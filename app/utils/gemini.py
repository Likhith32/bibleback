import os
import json
import re
import logging
from dotenv import load_dotenv
from google import genai

# Load .env HERE so the key is always available regardless of import order
load_dotenv()

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


class GeminiService:

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        self.client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized")

    async def get_response(self, prompt: str, is_json: bool = False):
        import asyncio

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                text = response.text
                if not text:
                    return None

                text = text.strip()

                if is_json:
                    try:
                        return json.loads(text)
                    except Exception:
                        cleaned = re.sub(r"```(?:json)?\s*", "", text)
                        cleaned = re.sub(r"```", "", cleaned).strip()
                        try:
                            return json.loads(cleaned)
                        except Exception:
                            logger.warning("JSON parse failed - raw: %s", text[:500])
                            return None

                return text

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "retryDelay" in error_str:
                    if attempt < 2:  # only wait if more attempts remain
                        wait = 15 * (attempt + 1)
                        logger.warning("Rate limited - waiting %ss", wait)
                        await asyncio.sleep(wait)
                        continue
                    # Last attempt failed
                    raise RateLimitError(
                        "Gemini API rate limit reached after 3 retries. Please wait a moment and try again."
                    )
                logger.error("Gemini error: %s", e, exc_info=True)
                return None


try:
    gemini_service = GeminiService()
except Exception as e:
    print(f"FAILED to create gemini_service: {e}", flush=True)
    gemini_service = None
