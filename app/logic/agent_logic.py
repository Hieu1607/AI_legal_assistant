"""
Agent business logic for processing legal questions.
Contains the core logic for multi-step agent processing.
"""

import asyncio
import os
import sys
import time
from typing import List, Optional, Union

# Set up logging
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from app.constants.http_status import (
    HTTP_STATUS_BAD_REQUEST,
    HTTP_STATUS_INTERNAL_SERVER_ERROR,
    HTTP_STATUS_OK,
    HTTP_STATUS_REQUEST_TIMEOUT,
)
from app.models.base_model import AgentRequest, AgentResponse
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


class AgentProcessor:
    """
    Core agent processor for handling legal question processing.
    Implements multi-step processing with timeout and error handling.
    """

    def __init__(self):
        """Initialize the agent processor."""
        self.logger = logger

    async def process_request(self, request: AgentRequest) -> AgentResponse:
        """
        Process legal question with configurable steps and timeout.

        Args:
            request: Agent request containing question, top_k, total_steps, and timeout

        Returns:
            AgentResponse: Response with success status, completed step, data, and execution time
        """
        start_time = time.time()
        self.logger.info(
            "Starting agent request with %d steps, timeout: %ds",
            request.total_steps,
            request.timeout_sec,
        )
        self.logger.info("Question: %s", request.question)

        chunks = []
        answer = ""
        formatted_answer = None
        step_completed = 0

        try:
            # Step 1: Retrieve relevant law chunks
            if request.total_steps >= 1:
                step1_result = await self._execute_step_1(request, start_time)
                if isinstance(step1_result, AgentResponse):
                    return step1_result  # Return error response

                step_completed, chunks = step1_result
                if request.total_steps == 1:
                    return self._create_response(
                        True,
                        HTTP_STATUS_OK,
                        step_completed,
                        chunks,
                        "Successfully retrieved law chunks",
                        start_time,
                    )

            # Step 2: Generate answer
            if request.total_steps >= 2:
                step2_result = await self._execute_step_2(
                    request, chunks, step_completed, start_time
                )
                if isinstance(step2_result, AgentResponse):
                    return step2_result  # Return error response

                step_completed, answer = step2_result
                if request.total_steps == 2:
                    return self._create_response(
                        True,
                        HTTP_STATUS_OK,
                        step_completed,
                        answer,
                        "Successfully generated answer",
                        start_time,
                    )

            # Step 3: Format citation
            if request.total_steps >= 3:
                step3_result = await self._execute_step_3(
                    request, chunks, answer, step_completed, start_time
                )
                if isinstance(step3_result, AgentResponse):
                    return step3_result  # Return error response

                step_completed, formatted_answer = step3_result
                return self._create_response(
                    True,
                    HTTP_STATUS_OK,
                    step_completed,
                    formatted_answer,
                    "Successfully formatted answer with citations",
                    start_time,
                )

        except (OSError, ValueError, RuntimeError) as e:
            return self._handle_unexpected_error(
                e, step_completed, chunks, answer, start_time
            )

        # Fallback return (should not reach here)
        total_time = time.time() - start_time
        self.logger.warning("Reached fallback return - this should not happen")
        return AgentResponse(
            success=False,
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            step_completed=step_completed,
            data=None,
            message="Unknown error occurred",
            execution_time=total_time,
        )

    async def _execute_step_1(
        self, request: AgentRequest, start_time: float
    ) -> Union[tuple[int, List], AgentResponse]:
        """
        Execute Step 1: Retrieve relevant law chunks.

        Returns:
            Either (step_completed, chunks) on success or AgentResponse on error
        """
        self.logger.info("Starting Step 1: Retrieving law chunks")
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
            self.logger.info(
                "Step 1 completed in %.2fs, retrieved %d chunks",
                step_time,
                len(chunks),
            )
            return step_completed, chunks

        except asyncio.TimeoutError:
            total_time = time.time() - start_time
            self.logger.error("Step 1 timed out after %ds", request.timeout_sec)
            return AgentResponse(
                success=False,
                status_code=HTTP_STATUS_REQUEST_TIMEOUT,
                step_completed=0,
                data=None,
                message=f"Step 1 (retrieve chunks) timed out after {request.timeout_sec}s",
                execution_time=total_time,
            )

    async def _execute_step_2(
        self,
        request: AgentRequest,
        chunks: List,
        step_completed: int,
        start_time: float,
    ) -> Union[tuple[int, str], AgentResponse]:
        """
        Execute Step 2: Generate answer.

        Returns:
            Either (step_completed, answer) on success or AgentResponse on error
        """
        if not chunks:
            total_time = time.time() - start_time
            self.logger.error("Cannot proceed to step 2: chunks is empty")
            return AgentResponse(
                success=False,
                status_code=HTTP_STATUS_BAD_REQUEST,
                step_completed=step_completed,
                data=None,
                message="Cannot generate answer: no chunks retrieved from step 1",
                execution_time=total_time,
            )

        self.logger.info("Starting Step 2: Generating answer")
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
            self.logger.info("Step 2 completed in %.2fs", step_time)
            return step_completed, answer

        except asyncio.TimeoutError:
            total_time = time.time() - start_time
            self.logger.error("Step 2 timed out after %ds", request.timeout_sec)
            return AgentResponse(
                success=False,
                status_code=HTTP_STATUS_REQUEST_TIMEOUT,
                step_completed=step_completed,
                data=chunks,  # Return chunks from step 1
                message=f"Step 2 (generate answer) timed out after {request.timeout_sec}s. Returning chunks from step 1.",
                execution_time=total_time,
            )

    async def _execute_step_3(
        self,
        request: AgentRequest,
        chunks: List,
        answer: str,
        step_completed: int,
        start_time: float,
    ) -> Union[tuple[int, Optional[str]], AgentResponse]:
        """
        Execute Step 3: Format citation.

        Returns:
            Either (step_completed, formatted_answer) on success or AgentResponse on error
        """
        if not chunks or not answer:
            total_time = time.time() - start_time
            self.logger.error("Cannot proceed to step 3: missing chunks or answer")
            return AgentResponse(
                success=False,
                status_code=HTTP_STATUS_BAD_REQUEST,
                step_completed=step_completed,
                data=answer if answer else chunks,
                message="Cannot format citation: missing data from previous steps",
                execution_time=total_time,
            )

        self.logger.info("Starting Step 3: Formatting citation")
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
            self.logger.info("Step 3 completed in %.2fs", step_time)
            return step_completed, formatted_answer

        except asyncio.TimeoutError:
            total_time = time.time() - start_time
            self.logger.error("Step 3 timed out after %ds", request.timeout_sec)
            return AgentResponse(
                success=False,
                status_code=HTTP_STATUS_REQUEST_TIMEOUT,
                step_completed=step_completed,
                data=answer,  # Return answer from step 2
                message=f"Step 3 (format citation) timed out after {request.timeout_sec}s. Returning answer from step 2.",
                execution_time=total_time,
            )

    def _create_response(
        self,
        success: bool,
        status_code: int,
        step_completed: int,
        data,
        message: str,
        start_time: float,
    ) -> AgentResponse:
        """Create standardized response."""
        total_time = time.time() - start_time
        self.logger.info("Request completed successfully in %.2fs", total_time)
        return AgentResponse(
            success=success,
            status_code=status_code,
            step_completed=step_completed,
            data=data,
            message=message,
            execution_time=total_time,
        )

    def _handle_unexpected_error(
        self,
        error: Exception,
        step_completed: int,
        chunks: List,
        answer: str,
        start_time: float,
    ) -> AgentResponse:
        """Handle unexpected errors and return partial results."""
        total_time = time.time() - start_time
        self.logger.error(
            "Unexpected error in step %d: %s",
            step_completed + 1,
            str(error),
            exc_info=True,
        )

        # Return partial results based on completed steps
        partial_data = None
        if step_completed >= 1:
            partial_data = chunks
        if step_completed >= 2:
            partial_data = answer

        return AgentResponse(
            success=False,
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            step_completed=step_completed,
            data=partial_data,
            message=f"Error occurred: {str(error)}. Returning partial results.",
            execution_time=total_time,
        )
