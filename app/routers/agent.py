"""
Agent router for handling legal question API endpoints.
Contains FastAPI router for agent-related endpoints.
"""

import os
import sys

from fastapi import APIRouter

# Set up logging
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from app.logic.agent_logic import AgentProcessor
from app.models.base_model import AgentRequest, AgentResponse

router = APIRouter()

# Initialize agent processor
agent_processor = AgentProcessor()


@router.post("/agent", response_model=AgentResponse)
async def ask_agent(request: AgentRequest):
    """
    Process legal question with configurable steps and timeout.

    This endpoint processes legal questions through multiple steps:
    1. Retrieve relevant law chunks from the database
    2. Generate an answer using AI based on retrieved chunks
    3. Format the answer with proper citations

    Args:
        request: Agent request containing:
            - question: Legal question to process (10-1000 characters)
            - top_k: Number of top relevant chunks to retrieve (1-20)
            - total_steps: Number of steps to execute (1-3)
            - timeout_sec: Timeout for each step in seconds (5-300)

    Returns:
        AgentResponse: Response containing:
            - success: Whether the request was successful
            - status_code: HTTP status code
            - step_completed: Number of steps successfully completed
            - data: Response data (varies by step completed)
            - message: Human-readable message
            - execution_time: Total execution time in seconds

    Examples:
        For step 1 only (retrieve chunks):
        ```json
        {
            "question": "Chương II điều 29 bộ luật hàng hải nói gì?",
            "top_k": 5,
            "total_steps": 1,
            "timeout_sec": 20
        }
        ```

        For full processing (all 3 steps):
        ```json
        {
            "question": "Tuổi tối thiểu để kết hôn là bao nhiêu?",
            "top_k": 3,
            "total_steps": 3,
            "timeout_sec": 30
        }
        ```
    """
    return await agent_processor.process_request(request)
