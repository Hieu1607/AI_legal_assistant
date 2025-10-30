"""
Weaviate tool integration for vector database operations.
"""

from typing import Optional
import os
import sys
from functools import lru_cache
from typing import Any, Dict, List

import dotenv
import weaviate
from weaviate.agents.query import QueryAgent
from weaviate.classes.init import Auth

# Load environment variables
dotenv.load_dotenv()
# Add root to sys.path for local imports
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.append(root)

SYS_PROMPT = """
Với vai trò là một trợ lý ảo pháp luật chuyên nghiệp, trả lời câu hỏi sau theo 3 trường hợp:
- Nếu tìm thấy nội dung thích hợp trong tài liệu, trả lời theo cấu trúc 'Theo [nguồn], [nội dung trích dẫn được diễn giải lại]'. Ví dụ: 'Theo chương I điều 1 luật tố tụng dân sự mới nhất, ...'
- Nếu không tìm thấy nội dung để trả lời chính xác, trả lời: 'Tôi chưa thể tìm thấy thông tin phù hợp trong tài liệu. Vui lòng đặt câu hỏi rõ ràng hơn hoặc tham khảo ý kiến chuyên gia pháp luật.'
- Nếu câu hỏi linh tinh, không liên quan đến pháp luật, trả lời: 'Tôi là trợ lý ảo pháp luật, vui lòng đặt câu hỏi liên quan đến lĩnh vực pháp luật.'

Câu hỏi:
"""

from app.configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

systemPrompt = os.getenv(
    "SYSTEM_PROMPT",
    SYS_PROMPT,
)


class WeaviateSearcher:
    def __init__(self):
        self.client = None
        self.query_agent = None

    def connect(self) -> bool:
        """Connect to Weaviate instance.
        Returns:
            bool: True if connection is successful, False otherwise.
        """
        try:
            weaviate_url = os.getenv("WEAVIATE_URL")
            api_key = os.getenv("WEAVIATE_API_KEY")

            if not weaviate_url or not api_key:
                logger.error(
                    "Weaviate URL or API key not set in environment variables."
                )
                return False

            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=Auth.api_key(api_key),  # type: ignore
            )

            # Test connection
            if self.client.is_ready():
                logger.info("Connected to Weaviate successfully.")
                return True
            logger.error("Failed to connect to Weaviate.")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Weaviate: {e}")
            self.client = None
            self.query_agent = None
            return False

    def _extract_chunks_from_response(self, response) -> List[Dict[str, Any]]:
        """Extract relevant information from fetched object.
        Args:
            obj (dict): The object fetched from Weaviate.

        Returns:
            dict: A dictionary containing the extracted information.
        """
        try:
            if response.sources:
                logger.info(f"Found {len(response.sources)} sources for the response.")
                relevant_chunks = []
                for i, source in enumerate(response.sources):
                    if hasattr(source, "collection") and hasattr(source, "object_id"):
                        if not self.client:
                            logger.error("Weaviate client is not connected.")
                            continue
                        collection = self.client.collections.get(source.collection)
                        obj = collection.query.fetch_object_by_id(source.object_id)
                        properties = obj.properties if obj else {}
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
                return relevant_chunks
            return []
        except Exception as e:
            logger.error(f"Error while extracting chunks from response: {e}")
            return []

    def ask_question(self, query: str) -> Dict[str, Any]:
        """Ask a question to Weaviate.
        Args:
            query (str): The question to ask.
        Returns:
            dict: Contains the answer and relevant chunks.
        """
        if not self.client:
            logger.info("Weaviate client is connecting...")
            if not self.connect():
                return {"error": "Failed to connect to Weaviate."}

        connection_opened = False
        try:
            if not self.client:
                if not self.connect():
                    return {
                        "answer": "Failed to connect to Weaviate.",
                        "relevant_chunks": [],
                    }
            connection_opened = True

            if not self.query_agent:
                try:
                    weaviate_agent = QueryAgent(  # type: ignore
                        client=self.client,  # type: ignore
                        collections=["LegalDocument"],
                        system_prompt=systemPrompt,
                    )
                    self.query_agent = weaviate_agent
                except Exception as e:
                    logger.error(f"Failed to create QueryAgent: {e}")
                    return {
                        "answer": "Failed to create QueryAgent.",
                        "relevant_chunks": [],
                    }

            # Query the agent
            response = self.query_agent.ask(query)
            answer = (
                response.final_answer if response.final_answer else "No answer found."
            )
            relevant_chunks = self._extract_chunks_from_response(response)
            if not relevant_chunks:
                logger.info("No sources found for the response.")
                relevant_chunks = []
            logger.info(f'Query Agent successfully answered the question: "{query}"')
            return {"answer": answer.strip(), "relevant_chunks": relevant_chunks}
        except Exception as e:
            logger.error(f"Error while asking question: {e}")
            return {
                "answer": "An error occurred while processing the question.",
                "relevant_chunks": [],
            }

    def close(self):
        """Close the Weaviate client connection."""
        if self.client:
            try:
                self.client.close()
                logger.info("Weaviate client connection closed.")
            except Exception as e:
                logger.error(f"Error while closing Weaviate client connection: {e}")
            finally:
                self.client = None
                self.query_agent = None


@lru_cache(maxsize=1)
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
