import asyncio
import json
from a2a.types import SendMessageSuccessResponse

from a2a.types import (
    AgentCard,
    Message,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TextPart,
    Role
)

import uuid
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import SendMessageSuccessResponse
from google.adk.tools.tool_context import ToolContext

from utils import send_message_to_agent

#TODO task config

kick_off_message = f"""
Launch the benchmark to assess the conceptual model generating ability of the agent located at http://localhost:8001/
"""

async def send_message(task: str, agent_url: str):
    PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"

    #state = tool_context.state
    #task_id = state.get("task_id", str(uuid.uuid4()))
    #context_id = state.get("context_id", str(uuid.uuid4()))
    #message_id = str(uuid.uuid4())

    async with httpx.AsyncClient(timeout=30) as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=agent_url,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            print(
                f"Fetching public agent card from: {agent_url}{PUBLIC_AGENT_CARD_PATH}"
            )
            _public_card = await resolver.get_agent_card()
            print("Fetched public agent card")
            print(_public_card.model_dump_json(indent=2))

            final_agent_card_to_use = _public_card

        except Exception as e:
            print(f"Error fetching public agent card: {e}")
            raise RuntimeError("Failed to fetch public agent card")

        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        print("A2AClient initialized")
        message_id = str(uuid.uuid4())
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
                #"taskId": task_id,
                #"contextId": context_id,
            },
        }

        message_request = SendMessageRequest(
            id=message_id, params=MessageSendParams.model_validate(payload)
        )

        # agent_url = agent_url  # TODO sync const variables for localhost
        # response = await send_message_to_agent(task, agent_url)

        logging.debug(f"message request {message_request}")
        send_response: SendMessageResponse = await client.send_message(message_request)
        logging.debug(f"send_response {send_response}")

        if not isinstance(
                send_response.root, SendMessageSuccessResponse
        ) or not isinstance(send_response.root.result, Task):
            print("Received a non-success or non-task response. Cannot proceed.")
            return

        response_content = send_response.root.model_dump_json(exclude_none=True)
        json_content = json.loads(response_content)

        resp = []
        if json_content.get("result", {}).get("artifacts"):
            for artifact in json_content["result"]["artifacts"]:
                if artifact.get("parts"):
                    resp.extend(artifact["parts"])
        return resp

async def send_message_(
        self, message_request: SendMessageRequest
    ) -> SendMessageResponse:
        return await self.agent_client.send_message(message_request)

async def main():
    agent_url = "http://localhost:9009/" #TODO sync const variables for localhost
    response = await send_message_(kick_off_message, agent_url)
    if response[0]['text']:
        response_text = response[0]['text']
        print("Agent reponse text:", response_text)
    else:
        print("Agent reponse:", response)



if __name__ == "__main__":
    import logging

    # Set up logging to see the raw request/response
    logging.basicConfig(
        format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG
    )
    # Specifically tune httpx to show body content
    logging.getLogger("httpx").setLevel(logging.DEBUG)
    logging.getLogger("httpcore").setLevel(logging.DEBUG)
    asyncio.run(main())