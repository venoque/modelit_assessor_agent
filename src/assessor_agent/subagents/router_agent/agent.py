from typing import Any
from pydantic import BaseModel, HttpUrl, ValidationError
#from a2a.server.tasks import TaskUpdater
#from a2a.types import Message, TaskState, Part, TextPart, DataPart
#from a2a.utils import get_message_text, new_agent_text_message

#from messenger import Messenger

from google.adk.agents import Agent, ParallelAgent, SequentialAgent
from a2a.client import A2AClient
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
import httpx

from dotenv import load_dotenv
import os
import uuid

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

load_dotenv()

import pandas as pd
import json

#from utils import send_message_to_agent
from a2a.types import SendMessageSuccessResponse
from google.adk.tools.tool_context import ToolContext



async def send_message_to_assessee_agent(task: str, agent_url: str): #, tool_context: ToolContext):
    """
    Use this tool to send a task to an external agent via its URL and retrieve the agent’s textual response.

    Inputs:
    - url (string): The base URL of the target agent.
    - task (string): The instruction or task to be executed by the agent.

    Behavior:
    - Sends the task to the agent asynchronously.
    - Waits for the agent’s response.
    - If the response is successful, extracts and returns the text content from the first response part.
    - If the response is not successful, returns the raw response for inspection.
    """

    PUBLIC_AGENT_CARD_PATH = "/.well-known/agent.json"

    #state = tool_context.state
    #task_id = state.get("task_id", str(uuid.uuid4()))
    #context_id = state.get("context_id", str(uuid.uuid4()))
    message_id = str(uuid.uuid4())

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

        #agent_url = agent_url  # TODO sync const variables for localhost
        #response = await send_message_to_agent(task, agent_url)

        send_response: SendMessageResponse = await client.send_message(message_request)
        print("send_response", send_response)

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

#TODO url
router_agent = Agent (
    name = "router_agent",
    model = "gemini-2.0-flash",
    description = "send a request to an assessee agent", #important for multiagent solutions. Other agents will read it
    instruction= """
    You are the assessor agent that evaluates conceptual models. 
    You give the task from the benchmark dataset to another agent via send_message_to_assessee_agent tool.
    The agent url is http://localhost:8001/
    The task is {task}.
    You receive a conceptual model in response.
    """,
    #sub_agents= [opm_evaluator, uml_evaluator], #tutorial 7
    tools = [send_message_to_assessee_agent], #tutorial 2
    #output_schema=EmailContent, #tutorial 4
    output_key="conceptual_model", #tutorial 4
    #before_agent_callback=before_agent_callback,
    #after_agent_callback=after_agent_callback, #tutorial 9,
)