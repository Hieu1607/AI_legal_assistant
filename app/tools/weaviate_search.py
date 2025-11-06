"""
Weaviate tool integration for vector database operations.
"""

import asyncio
from functools import lru_cache
from typing import Any, Dict, List, Optional

import weaviate
from weaviate.agents.query import AsyncQueryAgent
from weaviate.classes.init import Auth

from app.configs.logger import get_logger
from app.configs.settings import settings

logger = get_logger(__name__)

COLLECTION_NAME = settings.WEAVIATE_COLLECTION_NAME or "LegalDocument"
SYSTEM_PROMPT_PATH = settings.SYSTEM_PROMPT_PATH


@lru_cache(maxsize=1)
def load_system_prompt() -> str:
    """Load the system prompt from environment variable or file."""
    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


class WeaviateSearcher:
    def __init__(self):
        self.client = None
        self.query_agent = None

    async def connect(self, timeout: float = 10.0, retry: int = 1) -> bool:
        """Connect to Weaviate instance.
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            weaviate_url = settings.WEAVIATE_URL
            api_key = settings.WEAVIATE_API_KEY

            if not weaviate_url or not api_key:
                logger.error(
                    "Weaviate URL or API key not set in environment variables."
                )
                return False

            self.client = weaviate.use_async_with_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=Auth.api_key(api_key),  # type: ignore
            )
            for attempt in range(retry + 1):
                try:
                    await asyncio.wait_for(self.client.connect(), timeout=timeout)

                    if await self.client.is_ready():
                        logger.info("Connected to Weaviate successfully.")
                        return True

                    logger.error("Server not ready after connection.")
                    return False

                except asyncio.TimeoutError:
                    logger.warning(
                        f"Timeout while connecting (attempt {attempt + 1}/{retry + 1})"
                    )

                except Exception as e:
                    logger.error(f"Connection error: {e}")
                    break

            self.client = None  # Reset if fail
            logger.error("Failed to connect to Weaviate after retries.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            return False

    async def _extract_chunks_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract relevant information from fetched object.
        Args:
            obj (dict): The object fetched from Weaviate.

        Returns:
            dict: A dictionary containing the extracted information.
        """
        if not response.sources:
            return []

        relevant_chunks = []
        for i, source in enumerate(response.sources):
            try:
                collection = self.client.collections.get(source.collection)  # type: ignore
                obj = await collection.query.fetch_object_by_id(source.object_id)
                if not obj:
                    continue

                properties = obj.properties
                text = str(properties.get("text", ""))
                chunk_info = {
                    "text": text,
                    "title": properties.get("title", ""),
                    "chunk_id": properties.get("chunk_id", ""),
                    "date_of_issue": properties.get("date_of_issue", ""),
                    "update_day": properties.get("update_day", ""),
                    "uuid": source.object_id,
                }
                relevant_chunks.append(chunk_info)
                logger.info(
                    "Added chunk %d from fetched object property '%s'%s...",
                    i + 1,
                    source.collection,
                    text[:30] if text else "(no text)",
                )
            except Exception as e:
                logger.error(f"Error processing source {i+1}: {e}")

        return relevant_chunks

    async def ask_question(self, query: str) -> Dict[str, Any]:
        """Ask a question to Weaviate.
        Args:
            query (str): The question to ask.
        Returns:
            dict: Contains the answer and relevant chunks.
        """
        if not self.client:
            logger.info("Weaviate client is connecting...")
            if not await self.connect():
                return {
                    "answer": "Failed to connect to Weaviate.",
                    "relevant_chunks": [],
                }

        try:

            if not self.query_agent:
                try:
                    weaviate_agent = AsyncQueryAgent(  # type: ignore
                        client=self.client,  # type: ignore
                        collections=["LegalDocument"],
                        system_prompt=load_system_prompt(),
                    )
                    self.query_agent = weaviate_agent
                except Exception as e:
                    logger.error(f"Failed to create QueryAgent: {e}")
                    return {
                        "answer": "Failed to create QueryAgent.",
                        "relevant_chunks": [],
                    }

            # Query the agent
            response = await self.query_agent.ask(query)
            answer = (
                response.final_answer if response.final_answer else "No answer found."
            )
            relevant_chunks = await self._extract_chunks_from_response(response)
            if not relevant_chunks:
                logger.info("No sources found for the response.")
                relevant_chunks = []
            logger.info(
                f'Query Agent successfully answered the question: "{query[:10]}..."'
            )
            return {"answer": answer.strip(), "relevant_chunks": relevant_chunks}
        except Exception as e:
            logger.error(f"Error while asking question: {e}")
            return {
                "answer": "An error occurred while processing the question.",
                "relevant_chunks": [],
            }

    async def close(self):
        """Close the Weaviate client connection."""
        if self.client:
            try:
                await self.client.close()
                logger.info("Weaviate client connection closed.")
            except Exception as e:
                logger.error(f"Error while closing Weaviate client connection: {e}")
            finally:
                self.client = None
                self.query_agent = None


# Singleton instance (module-level)
searcher_instance: WeaviateSearcher | None = None


@lru_cache(1)
def get_searcher() -> Optional[WeaviateSearcher]:
    """Get an instance of WeaviateSearcher.
    Returns:
        WeaviateSearcher: An instance of WeaviateSearcher.
    """
    try:
        logger.info("Creating WeaviateSearcher instance...")
        return WeaviateSearcher()
    except Exception as e:
        logger.error(f"Error while creating WeaviateSearcher instance: {e}")
        return None
