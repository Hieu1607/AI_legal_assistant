import asyncio
import os
import sys
import time
from typing import Any

from fastapi import APIRouter

# from fastapi import Request
# from fastapi.exceptions import RequestValidationError
# from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# Set up logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from configs.logger import get_logger_agent
from services.tools import (
    FormatInput,
    GenerateInput,
    RetrieveInput,
    format_citation,
    generate_answer,
    retrieve_laws,
)

logger = get_logger_agent(__name__)

router = APIRouter()


class AgentRequest(BaseModel):
    question: str = Field(
        default="Chương II điều 29 bộ luật hàng hải nói gì?",
        min_length=10,
        max_length=1000,
        description="Legal question to ask the agent (10-1000 characters)",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top relevant chunks to retrieve (1-20)",
    )
    total_steps: int = Field(
        default=3, ge=1, le=3, description="Total number of steps to execute (1-3)"
    )
    timeout_sec: int = Field(
        default=20, ge=5, le=300, description="Timeout for each step in seconds (5-300)"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v):
        if not v or v.isspace():
            raise ValueError("Question cannot be empty or only whitespace")
        return v.strip()

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v):
        if v < 1:
            raise ValueError("top_k must be at least 1")
        if v > 20:
            raise ValueError("top_k cannot exceed 20")
        return v

    @field_validator("total_steps")
    @classmethod
    def validate_total_steps(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError("total_steps must be 1, 2, or 3")
        return v

    @field_validator("timeout_sec")
    @classmethod
    def validate_timeout(cls, v):
        if v < 5:
            raise ValueError("timeout_sec must be at least 5 seconds")
        if v > 300:
            raise ValueError("timeout_sec cannot exceed 300 seconds (5 minutes)")
        return v


class AgentResponse(BaseModel):
    success: bool
    status_code: int
    step_completed: int
    data: Any
    message: str
    execution_time: float


@router.post("/agent", response_model=AgentResponse)
async def ask_agent(request: AgentRequest):
    """
    Process legal question with configurable steps and timeout.

    Args:
        request: Agent request containing question, top_k, total_steps, and timeout

    Returns:
        AgentResponse: Response with success status, completed step, data, and execution time
    """
    start_time = time.time()
    logger.info(
        "Starting agent request with %d steps, timeout: %ds",
        request.total_steps,
        request.timeout_sec,
    )
    logger.info("Question: %s", request.question)

    chunks = []
    answer = ""
    formatted_answer = None
    step_completed = 0

    try:
        # Step 1: Retrieve relevant law chunks
        if request.total_steps >= 1:
            logger.info("Starting Step 1: Retrieving law chunks")
            step_start = time.time()

            try:
                chunks = await asyncio.wait_for(
                    asyncio.to_thread(
                        retrieve_laws,
                        RetrieveInput(question=request.question, top_k=request.top_k),
                    ),
                    timeout=request.timeout_sec,
                )
                chunks = chunks.chunks
                step_completed = 1
                step_time = time.time() - step_start
                logger.info(
                    "Step 1 completed in %.2fs, retrieved %d chunks",
                    step_time,
                    len(chunks),
                )

                if request.total_steps == 1:
                    total_time = time.time() - start_time
                    logger.info("Request completed successfully in %.2fs", total_time)
                    return AgentResponse(
                        success=True,
                        status_code=200,
                        step_completed=step_completed,
                        data=chunks,
                        message="Successfully retrieved law chunks",
                        execution_time=total_time,
                    )

            except asyncio.TimeoutError:
                total_time = time.time() - start_time
                logger.error("Step 1 timed out after %ds", request.timeout_sec)
                return AgentResponse(
                    success=False,
                    status_code=408,
                    step_completed=step_completed,
                    data=None,
                    message=f"Step 1 (retrieve chunks) timed out after {request.timeout_sec}s",
                    execution_time=total_time,
                )

        # Step 2: Generate answer
        if request.total_steps >= 2 and chunks != []:
            logger.info("Starting Step 2: Generating answer")
            step_start = time.time()

            try:
                result = await asyncio.wait_for(
                    generate_answer(
                        GenerateInput(question=request.question, chunks=chunks)
                    ),
                    timeout=request.timeout_sec,
                )
                answer = result.answer
                step_completed = 2
                step_time = time.time() - step_start
                logger.info("Step 2 completed in %.2fs", step_time)

                if request.total_steps == 2:
                    total_time = time.time() - start_time
                    logger.info("Request completed successfully in %.2fs", total_time)
                    return AgentResponse(
                        success=True,
                        status_code=200,
                        step_completed=step_completed,
                        data=answer,
                        message="Successfully generated answer",
                        execution_time=total_time,
                    )

            except asyncio.TimeoutError:
                total_time = time.time() - start_time
                logger.error("Step 2 timed out after %ds", request.timeout_sec)
                return AgentResponse(
                    success=False,
                    status_code=408,
                    step_completed=step_completed,
                    data=chunks,  # Return chunks from step 1
                    message=f"Step 2 (generate answer) timed out after {request.timeout_sec}s. Returning chunks from step 1.",
                    execution_time=total_time,
                )
        elif request.total_steps >= 2 and chunks == []:
            total_time = time.time() - start_time
            logger.error("Cannot proceed to step 2: chunks is None")
            return AgentResponse(
                success=False,
                status_code=400,
                step_completed=step_completed,
                data=None,
                message="Cannot generate answer: no chunks retrieved from step 1",
                execution_time=total_time,
            )

        # Step 3: Format citation
        if request.total_steps >= 3 and chunks != [] and answer != "":
            logger.info("Starting Step 3: Formatting citation")
            step_start = time.time()

            try:
                formatted_result = await asyncio.wait_for(
                    asyncio.to_thread(
                        format_citation, FormatInput(answer=answer, chunks=chunks)
                    ),
                    timeout=request.timeout_sec,
                )
                formatted_answer = formatted_result.formatted_answer
                step_completed = 3
                step_time = time.time() - step_start
                logger.info("Step 3 completed in %.2fs", step_time)

                total_time = time.time() - start_time
                logger.info("Request completed successfully in %.2fs", total_time)
                return AgentResponse(
                    success=True,
                    status_code=200,
                    step_completed=step_completed,
                    data=formatted_answer,
                    message="Successfully formatted answer with citations",
                    execution_time=total_time,
                )

            except asyncio.TimeoutError:
                total_time = time.time() - start_time
                logger.error("Step 3 timed out after %ds", request.timeout_sec)
                return AgentResponse(
                    success=False,
                    status_code=408,
                    step_completed=step_completed,
                    data=answer,  # Return answer from step 2
                    message=f"Step 3 (format citation) timed out after {request.timeout_sec}s. Returning answer from step 2.",
                    execution_time=total_time,
                )
        elif request.total_steps >= 3 and (chunks == [] or answer == ""):
            total_time = time.time() - start_time
            logger.error("Cannot proceed to step 3: missing chunks or answer")
            return AgentResponse(
                success=False,
                status_code=400,
                step_completed=step_completed,
                data=answer if answer is not None else chunks,
                message="Cannot format citation: missing data from previous steps",
                execution_time=total_time,
            )

    except (OSError, ValueError, RuntimeError) as e:
        total_time = time.time() - start_time
        logger.error(
            "Unexpected error in step %d: %s", step_completed + 1, str(e), exc_info=True
        )

        # Return partial results based on completed steps
        partial_data = None
        if step_completed >= 1:
            partial_data = chunks
        if step_completed >= 2:
            partial_data = answer

        return AgentResponse(
            success=False,
            status_code=500,
            step_completed=step_completed,
            data=partial_data,
            message=f"Error occurred: {str(e)}. Returning partial results.",
            execution_time=total_time,
        )

    # Fallback return (should not reach here)
    total_time = time.time() - start_time
    logger.warning("Reached fallback return - this should not happen")
    return AgentResponse(
        success=False,
        status_code=500,
        step_completed=step_completed,
        data=None,
        message="Unknown error occurred",
        execution_time=total_time,
    )
