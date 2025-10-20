"""
Weaviate Cloud search functionality for RAG using Query Agent
"""

import io
import os
import sys
from typing import Any, Dict, List

import weaviate

# Add project root to path
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger

logger = get_logger(__name__)

# Global searcher instance
_searcher = None


class WeaviateSearcher:
    """
    Weaviate Cloud searcher for legal documents using Query Agent.

    This class handles connection to Weaviate Cloud and provides
    RAG (Retrieval-Augmented Generation) functionality for legal queries.
    """

    def __init__(self):
        """Initialize Weaviate searcher with empty client and query agent."""
        self.client = None
        self.query_agent = None

    def connect(self) -> bool:
        """
        Connect to Weaviate Cloud.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Read Weaviate configuration from environment
            weaviate_url = os.getenv("WEAVIATE_URL")
            weaviate_api_key = os.getenv("WEAVIATE_API_KEY")

            if not weaviate_url or not weaviate_api_key:
                logger.error(
                    "Missing Weaviate configuration. "
                    "Please set WEAVIATE_URL and WEAVIATE_API_KEY"
                )
                return False

            # Initialize Weaviate client
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=weaviate_url,
                auth_credentials=weaviate.auth.AuthApiKey(weaviate_api_key),
            )

            # Test connection
            if self.client.is_ready():
                logger.info("Successfully connected to Weaviate Cloud")

                # Query Agent will be initialized when needed for RAG
                self.query_agent = None

                return True
            else:
                logger.error("Failed to connect to Weaviate Cloud")
                return False

        except Exception as e:
            logger.error("Error connecting to Weaviate: %s", str(e))
            self.client = None
            self.query_agent = None
            return False

    async def ask_question_with_context(self, query: str) -> dict:
        """
        Ask a question using Weaviate Query Agent and return answer with context.

        Args:
            query (str): The user's question

        Returns:
            dict: Contains both 'answer' and 'relevant_chunks'
        """
        connection_opened = False
        try:
            # Ensure connection is established
            if not self.client:
                if not self.connect():
                    return {
                        "answer": "Không thể kết nối đến cơ sở dữ liệu pháp luật.",
                        "relevant_chunks": [],
                    }
                connection_opened = True

            # Initialize Query Agent if not already done
            if not self.query_agent:
                try:
                    # pylint: disable=import-outside-toplevel
                    import weaviate_agents.query as wq

                    # Get the WeaviateQueryAgent class
                    weaviate_query_agent = getattr(wq, "WeaviateQueryAgent", None)
                    if not weaviate_query_agent:
                        # Try alternative names
                        for name in dir(wq):
                            if "QueryAgent" in name:
                                weaviate_query_agent = getattr(wq, name)
                                break

                    if weaviate_query_agent:
                        self.query_agent = weaviate_query_agent(
                            client=self.client, collections=["LegalDocument"]
                        )
                    else:
                        raise Exception("Could not find QueryAgent class")

                except Exception as e:
                    logger.error("Failed to initialize Query Agent: %s", e)
                    return {
                        "answer": "Không thể khởi tạo Query Agent.",
                        "relevant_chunks": [],
                    }

            # Add custom prompt to the query
            prompt = """Với vai trò là 1 trợ lý ảo pháp luật, vui lòng trả lời câu hỏi dựa trên thông tin được cung cấp. Chỉ sử dụng thông tin trong các bộ luật mới nhất để trả lời câu hỏi.

Trả lời câu hỏi theo 3 trường hợp:
Trường hợp 1: Nếu tìm thấy nội dung thích hợp trong tài liệu, trả lời 'Theo chương ... điều ... bộ luật abc ..., nội dung'
Trường hợp 2: Nếu không tìm thấy nội dung thích hợp trong tài liệu, trả lời: 'Không tìm thấy thông tin liên quan đến câu hỏi.'
Trường hợp 3: Nếu câu hỏi linh tinh hoặc không liên quan đến pháp luật, trả lời: "Chào bạn, tôi đã sẵn sàng trả lời với vai trò là một trợ lý ảo pháp luật. Tuy nhiên, có vẻ như bạn chưa cung cấp câu hỏi cụ thể hoặc câu hỏi của bạn không liên quan đến pháp luật. Vui lòng đặt câu hỏi lại để tôi có thể trả lời."
Trả lời ngắn gọn.

Câu hỏi: """  # pylint: disable=line-too-long

            # Combine prompt with original query
            new_query = prompt + query

            # Use Query Agent to get answer (retrieval + generation in one step)
            response = await self.query_agent.ask(new_query)

            # Extract the text response from the QueryAgentResponse object
            answer = self._extract_answer_from_response(response)

            # Extract relevant chunks from response (now returns dict with metadata)
            # IMPORTANT: Extract chunks while client connection is still active
            relevant_chunks = self._extract_chunks_from_response(response)

            logger.info("Query Agent successfully processed question: %s", query)
            return {"answer": answer.strip(), "relevant_chunks": relevant_chunks}

        except Exception as e:
            logger.error("Error with Query Agent: %s", str(e))
            return {
                "answer": "Đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại.",
                "relevant_chunks": [],
            }
        finally:
            # Only close connection if we opened it in this method call
            # This prevents premature closing when used from rag_logic
            if connection_opened and self.client:
                try:
                    self.client.close()
                    logger.info("Closed Weaviate connection")
                except Exception as e:
                    logger.warning("Error closing Weaviate connection: %s", e)
                finally:
                    self.client = None
                    self.query_agent = None

    async def ask_question(self, query: str) -> str:
        """
        Ask a question using Weaviate Query Agent (backward compatibility).

        Args:
            query (str): The user's question

        Returns:
            str: Generated answer from the Query Agent
        """
        result = await self.ask_question_with_context(query)
        return result["answer"]

    def _extract_answer_from_response(self, response) -> str:
        """
        Extract answer text from Query Agent response.

        Args:
            response: Query Agent response object

        Returns:
            str: Extracted answer text
        """
        if hasattr(response, "response") and hasattr(response.response, "content"):
            return response.response.content
        elif hasattr(response, "content"):
            return response.content
        elif hasattr(response, "text"):
            return response.text
        else:
            # Try to get the final answer from the response structure
            try:
                if hasattr(response, "final_answer"):
                    return response.final_answer
                elif hasattr(response, "answer"):
                    return response.answer
                else:
                    # If response has display method, use that
                    if hasattr(response, "display"):

                        old_stdout = sys.stdout
                        sys.stdout = buffer = io.StringIO()
                        response.display()
                        sys.stdout = old_stdout
                        return buffer.getvalue()
                    else:
                        logger.warning(
                            "Could not extract answer from response type: %s",
                            type(response),
                        )
                        return "Không thể trích xuất câu trả lời từ Query Agent."
            except Exception as e:
                logger.error("Error extracting answer from response: %s", e)
                return "Lỗi khi xử lý phản hồi từ Query Agent."

    def _extract_chunks_from_response(self, response) -> List[Dict[str, Any]]:
        """
        Extract relevant document chunks with metadata from Query Agent response.

        Args:
            response: Query Agent response object

        Returns:
            List[Dict[str, Any]]: List of document chunks with metadata
        """
        try:
            chunks = []

            # Debug logging to understand response structure
            logger.info("Response type: %s", type(response))
            logger.info("Response attributes: %s", dir(response))

            # Method 1: Try to extract from response.searches (recommended approach)
            if hasattr(response, "searches") and response.searches:
                logger.info("Found %d searches in response", len(response.searches))
                for i, search in enumerate(response.searches):
                    logger.info("Search %d attributes: %s", i, dir(search))
                    # Check if search has objects with content
                    if hasattr(search, "objects") and search.objects:
                        logger.info("Search %d has %d objects", i, len(search.objects))
                        for j, obj in enumerate(search.objects):
                            if hasattr(obj, "properties"):
                                properties = obj.properties
                                logger.info(
                                    "Object %d properties keys: %s",
                                    j,
                                    list(properties.keys()),
                                )
                                # Look for text content in common property names
                                for prop_name in ["text", "content", "chunk", "data"]:
                                    if prop_name in properties:
                                        text_content = properties[prop_name]
                                        if text_content:
                                            chunk_info = {
                                                "text": text_content,
                                                "title": properties.get(
                                                    "title", "Không có tiêu đề"
                                                ),
                                                "chunk_id": properties.get(
                                                    "chunk_id", f"chunk_{len(chunks)}"
                                                ),
                                                "date_of_issue": properties.get(
                                                    "date_of_issue", ""
                                                ),
                                                "update_day": properties.get(
                                                    "update_day", ""
                                                ),
                                                "uuid": (
                                                    str(obj.uuid)
                                                    if hasattr(obj, "uuid")
                                                    else ""
                                                ),
                                            }
                                            # Check if this chunk is not already added
                                            if not any(
                                                existing["text"] == text_content
                                                for existing in chunks
                                            ):
                                                chunks.append(chunk_info)
                                                text_preview = (
                                                    str(text_content)[:100]
                                                    if text_content
                                                    else ""
                                                )
                                                logger.info(
                                                    "Added chunk from property '%s': %s...",
                                                    prop_name,
                                                    text_preview,
                                                )
                                            break

            # Method 2: Extract chunks from sources using object_id (fallback)
            if not chunks and hasattr(response, "sources") and response.sources:
                logger.info("Found %d sources in response", len(response.sources))
                for i, source in enumerate(response.sources):
                    logger.info("Source %d attributes: %s", i, dir(source))
                    # Extract object_id and collection from source
                    if hasattr(source, "object_id") and hasattr(source, "collection"):
                        object_id = source.object_id
                        collection_name = source.collection
                        logger.info(
                            "Source %d: object_id=%s, collection=%s",
                            i,
                            object_id,
                            collection_name,
                        )

                        try:
                            # Query Weaviate directly to get object content
                            if not self.client:
                                logger.error("Weaviate client not initialized")
                                continue

                            if not hasattr(self.client, "collections"):
                                logger.error(
                                    "Weaviate client does not have collections"
                                )
                                continue

                            collection = self.client.collections.get(collection_name)
                            obj = collection.query.fetch_object_by_id(object_id)

                            if obj and hasattr(obj, "properties"):
                                properties = obj.properties
                                logger.info(
                                    "Fetched object properties keys: %s",
                                    list(properties.keys()),
                                )
                                # Look for text content in common property names
                                for prop_name in ["text", "content", "chunk", "data"]:
                                    if prop_name in properties:
                                        text_content = properties[prop_name]
                                        if text_content:
                                            chunk_info = {
                                                "text": text_content,
                                                "title": properties.get(
                                                    "title", "Không có tiêu đề"
                                                ),
                                                "chunk_id": properties.get(
                                                    "chunk_id", object_id
                                                ),
                                                "date_of_issue": properties.get(
                                                    "date_of_issue", ""
                                                ),
                                                "update_day": properties.get(
                                                    "update_day", ""
                                                ),
                                                "uuid": object_id,
                                            }
                                            # Check if this chunk is not already added
                                            if not any(
                                                existing["text"] == text_content
                                                for existing in chunks
                                            ):
                                                chunks.append(chunk_info)
                                                text_preview = (
                                                    str(text_content)[:100]
                                                    if text_content
                                                    else ""
                                                )
                                                logger.info(
                                                    "Added chunk from fetched object property '%s': %s...",
                                                    prop_name,
                                                    text_preview,
                                                )
                                            break

                        except Exception as e:
                            logger.error("Error fetching object %s: %s", object_id, e)

            # Method 3: If we still don't have chunks, try a simple BM25 search as fallback
            if not chunks:
                logger.warning(
                    "No chunks found in Query Agent response, using BM25 search as fallback"
                )
                try:
                    # Get a simple BM25 search result as context
                    if not self.client:
                        logger.error("Weaviate client not initialized")
                        return chunks

                    if not hasattr(self.client, "collections"):
                        logger.error("Weaviate client does not have collections")
                        return chunks

                    collection = self.client.collections.get("LegalDocument")
                    bm25_response = collection.query.bm25(
                        query=(
                            response.response.content[:100]
                            if hasattr(response, "response")
                            and hasattr(response.response, "content")
                            else "pháp luật"
                        ),
                        limit=3,
                    )

                    for obj in bm25_response.objects:
                        if hasattr(obj, "properties"):
                            properties = obj.properties
                            for prop_name in ["text", "content", "chunk", "data"]:
                                if prop_name in properties:
                                    text_content = properties[prop_name]
                                    if text_content:
                                        chunk_info = {
                                            "text": text_content,
                                            "title": properties.get(
                                                "title", "Không có tiêu đề"
                                            ),
                                            "chunk_id": properties.get(
                                                "chunk_id", f"fallback_{len(chunks)}"
                                            ),
                                            "date_of_issue": properties.get(
                                                "date_of_issue", ""
                                            ),
                                            "update_day": properties.get(
                                                "update_day", ""
                                            ),
                                            "uuid": (
                                                str(obj.uuid)
                                                if hasattr(obj, "uuid")
                                                else ""
                                            ),
                                        }
                                        # Check if this chunk is not already added
                                        if not any(
                                            existing["text"] == text_content
                                            for existing in chunks
                                        ):
                                            chunks.append(chunk_info)
                                            text_preview = (
                                                str(text_content)[:100]
                                                if text_content
                                                else ""
                                            )
                                            logger.info(
                                                "Added fallback chunk from BM25 search: %s...",
                                                text_preview,
                                            )
                                        break
                except Exception as e:
                    logger.error("Error in fallback BM25 search: %s", e)

            logger.info("Total chunks extracted: %d", len(chunks))
            return chunks

        except Exception as e:
            logger.error("Error extracting chunks from response: %s", e)
            return []

    def search_relevant_documents(
        self, query: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using direct Weaviate vector search (not Query Agent).

        Args:
            query (str): The search query
            limit (int): Maximum number of results to return

        Returns:
            List[Dict[str, Any]]: List of document dictionaries with text, title, chunk_id, etc.
        """
        try:
            if not self.client:
                if not self.connect():
                    return []

            # Get the collection
            if self.client and hasattr(self.client, "collections"):
                collection = self.client.collections.get("LegalDocument")
            else:
                logger.error("Weaviate client not initialized")
                return []

            # Perform BM25 keyword search (since vector search is not configured)
            response = collection.query.bm25(query=query, limit=limit)

            # Extract document information from results
            documents = []
            for obj in response.objects:
                if hasattr(obj, "properties"):
                    properties = obj.properties

                    # Extract text content
                    text_content = None
                    for prop_name in ["text", "content", "chunk", "data"]:
                        if prop_name in properties and properties[prop_name]:
                            text_content = properties[prop_name]
                            break

                    if text_content:
                        doc_info = {
                            "text": text_content,
                            "title": properties.get("title", "Không có tiêu đề"),
                            "chunk_id": properties.get(
                                "chunk_id", f"chunk_{len(documents)}"
                            ),
                            "date_of_issue": properties.get("date_of_issue", ""),
                            "update_day": properties.get("update_day", ""),
                            "uuid": str(obj.uuid) if hasattr(obj, "uuid") else "",
                        }
                        documents.append(doc_info)

            logger.info(
                "Found %d relevant documents for query: %s", len(documents), query
            )
            return documents

        except Exception as e:
            logger.error("Error in search_relevant_documents: %s", str(e))
            return []

    def close(self):
        """Close Weaviate connection"""
        if self.client:
            try:
                self.client.close()
                logger.info("Closed Weaviate connection")
            except Exception as e:
                logger.warning("Error closing Weaviate connection: %s", e)
            finally:
                self.client = None
                self.query_agent = None


def get_searcher() -> WeaviateSearcher:
    """Get singleton searcher instance"""
    global _searcher  # pylint: disable=global-statement
    if _searcher is None:
        _searcher = WeaviateSearcher()
    return _searcher


def search_relevant_embeddings(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search for relevant documents using Weaviate Cloud.

    This function maintains compatibility with the existing RAG interface.

    Args:
        query (str): The search query
        limit (int): Maximum number of results to return

    Returns:
        Dict[str, Any]: Response in standard format compatible with retrieve logic
    """
    searcher = None
    try:
        searcher = get_searcher()
        document_infos = searcher.search_relevant_documents(query, limit)

        # Extract text and metadata from document info dictionaries
        relevant_texts = [doc["text"] for doc in document_infos]

        # Enhanced metadata with title and other information
        metadatas = []
        for i, doc in enumerate(document_infos):
            metadata = {
                "source": "weaviate",
                "chunk_id": doc.get("chunk_id", f"chunk_{i}"),
                "title": doc.get("title", "Không có tiêu đề"),
                "date_of_issue": doc.get("date_of_issue", ""),
                "update_day": doc.get("update_day", ""),
                "uuid": doc.get("uuid", ""),
            }
            metadatas.append(metadata)

        # Format response for compatibility with existing RAG logic
        response = {
            "ids": [
                [
                    doc.get("chunk_id", f"chunk_{i}")
                    for i, doc in enumerate(document_infos)
                ]
            ],
            "documents": [relevant_texts],
            "metadatas": [metadatas],
            "distances": [
                [0.1 * (i + 1) for i in range(len(relevant_texts))]
            ],  # Placeholder distances
            "cosine_similarities": [
                [1.0 - (0.1 * (i + 1)) for i in range(len(relevant_texts))]
            ],  # Calculated similarities
        }

        return response

    except Exception as e:
        logger.error("Error in search_relevant_embeddings: %s", str(e))
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "cosine_similarities": [[]],
        }
    finally:
        # Ensure connection is closed
        if searcher:
            searcher.close()


def cleanup():
    """Cleanup function to close connections"""
    global _searcher  # pylint: disable=global-statement
    if _searcher:
        _searcher.close()
        _searcher = None


class WeaviateSearchContext:
    """Context manager for Weaviate search operations"""

    def __init__(self):
        self.searcher = None

    def __enter__(self):
        self.searcher = WeaviateSearcher()
        return self.searcher

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.searcher:
            self.searcher.close()
        return False
