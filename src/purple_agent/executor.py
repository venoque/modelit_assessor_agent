from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError,
    InvalidRequestError,
)
from a2a.utils.errors import ServerError
from a2a.utils import (
    new_agent_text_message,
    new_task,
)

from .agent import root_agent as assessor_agent

from a2a.utils.errors import ServerError

import logging
from collections.abc import AsyncGenerator
from google.adk import Runner
from google.adk.events import Event
from google.genai import types

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

from .converters import convert_genai_parts_to_a2a, convert_a2a_parts_to_genai


TERMINAL_STATES = {
    TaskState.completed,
    TaskState.canceled,
    TaskState.failed,
    TaskState.rejected
}


class Executor(AgentExecutor):
    """An AgentExecutor that runs ADK-based Green Agent."""

    def __init__(self, runner: Runner):
        # I don't understand
        #self.agent: assessor_agent# context_id to agent instance
        #mine
        self.runner = runner
        self._running_sessions = {}

    def _run_agent(
        self, session_id, new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        logger.debug("Running agent...")
        return self.runner.run_async(
            session_id=session_id, user_id="green_agent", new_message=new_message
        )

    async def _process_request(
            self,
            new_message: types.Content,
            session_id: str,
            task_updater: TaskUpdater,
    ) -> None:
        logger.debug("HERE I AM 1")
        session_obj = await self._upsert_session(session_id)
        session_id = session_obj.id
        logger.debug("HERE I AM 2")

        async for event in self._run_agent(session_id, new_message):
            if event.is_final_response():
                parts = convert_genai_parts_to_a2a(
                    event.content.parts if event.content and event.content.parts else []
                )
                logger.debug("Yielding final response: %s", parts)
                await task_updater.add_artifact(parts)
                await task_updater.complete()
                break
            if not event.get_function_calls():
                logger.debug("Yielding update response")
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(
                            event.content.parts
                            if event.content and event.content.parts
                            else []
                        ),
                    ),
                )
            else:
                logger.debug("Skipping event")

    async def execute(
            self,
            context: RequestContext,
            event_queue: EventQueue,
    ):
        print("Executing....")
        if not context.task_id or not context.context_id:
            raise ValueError("RequestContext must have task_id and context_id")
        if not context.message:
            raise ValueError("RequestContext must have a message")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        #if not context.current_task:
        #    updater.submit()
        await updater.start_work()
        logger.debug("Start processing request...")
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            context.context_id,
            updater,
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        logger.debug("Cancel request... OPERATION ERROR")
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        session = self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id="green_agent", session_id=session_id
        )
        if session is None:
            session = self.runner.session_service.create_session(
                app_name=self.runner.app_name,
                user_id="green_agent",
                session_id=session_id,
            )
        if session is None:
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


