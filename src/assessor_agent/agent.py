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

from .subagents.clarity_evaluator import clarity_evaluator
from .subagents.completeness_evaluator import compliteness_evaluator
from .subagents.result_synthesizer import result_synthesizer
from .subagents.router_agent import router_agent

#from utils import send_message_to_agent
from a2a.types import SendMessageSuccessResponse
from google.adk.tools.tool_context import ToolContext

# GLOBAL VARIABLES
# Get the directory where this script (agent.py) is located
script_dir = os.path.dirname(os.path.abspath(__file__))
# Build the full path to the dataset relative to the script
DATASET_PATH = os.path.join(script_dir, 'dataset.csv')

try:
    _df_init = pd.read_csv(DATASET_PATH)
    DATASET_LEN = len(_df_init)
    print(f"Dataset loaded. Total rows: {DATASET_LEN}")
except Exception as e:
    print(f"Error loading dataset length: {e}")
    DATASET_LEN = 0


class EvalRequest(BaseModel):
    """Request format sent by the AgentBeats platform to green agents."""
    participants: dict[str, HttpUrl] # role -> agent URL
    config: dict[str, Any]


# function that is used in the main Tool
def get_next_task(file_path: str, row_index: int) -> str:
    """
        Retrieves a row from a CSV file as a dictionary and returns it as a JSON string.
        Useful for getting specific details about an entry in a dataset.

        Args:
            file_path (str): The name or path of the CSV file.
            row_index (int): The 0-based index of the data row (0 is the first record after the header).

        Returns:
            str: A JSON string representation of the row, or an error message.
        """
    try:
        # Read the CSV (assuming first row is header)
        df = pd.read_csv(file_path)
        # Check bounds
        if row_index < 0 or row_index >= len(df):
            return json.dumps({
                "error": "STOP. Index out of bounds.",
                "status": "FINISHED",
                "message": f"You have reached the end of the dataset ({len(df)} rows). Do not attempt further tasks."
            })
        # Get the row as a dictionary
        row_dict = df.iloc[row_index].to_dict()
        # Return as JSON string
        return json.dumps(row_dict)
    except FileNotFoundError:
        return json.dumps({"error": "File not found."})
    except Exception as e:
        return json.dumps({"error": str(e)})

# TOOL to Get the next task from the benchmark dataset
# 2. Create the specific tool for the Agent
def get_benchmark_task(row_index: int) -> str:
    """
    Retrieves the specific benchmark task row from the configured dataset.
    Args:
        row_index (int): The 0-based index of the task to retrieve.
    """
    # Hardcode the path here, or load it from your environment/config
    dataset_path = DATASET_PATH
    return get_next_task(dataset_path, row_index)


#def before_agent_callback(callback_context: CallbackContext) -> Optional[types.Content]:
#    state = callback_context.state

#    # 1. Initialize the row_index
#    if "row_index" not in state:
#        state["row_index"] = 0
#    else:
#        current_index = state["row_index"]
#        # 2. Check if we have reached the end of the dataset
#        # If current index is the last one (length - 1), we cannot go further.
#        if current_index >= DATASET_LEN - 1:
#            print("End of dataset reached. Stopping assessment.")
#            state["finished"] = True  # Useful flag for other parts of your app
#            # Return a message to the agent/system
#            return types.Content(
#                role="model",
#                parts=[types.Part(text="System Notification: All tasks in the dataset have been processed.")]
#            )
#        else:
#            # Only increment if we are safe
#            state["row_index"] += 1
#            #print(f"Moving to the row: {state['row_index']}")
#           return None

#give the task
#collect answer
#process the results with different evaluation
#synthesize the result
#write into db
#{row_index}


task_giving_agent = Agent (
    name = "task_giving_agent",
    model = "gemini-2.0-flash",
    description = "green agent", #important for multiagent solutions. Other agents will read it
    instruction= """
    You are the assessor agent that evaluates conceptual models. 
    You extract the task with the tool get_benchmark_task and pass it further. The row_index is 1. 
    """,
    #sub_agents= [opm_evaluator, uml_evaluator], #tutorial 7
    tools = [get_benchmark_task], #tutorial 2
    #output_schema=EmailContent, #tutorial 4
    output_key="task", #tutorial 4
    #before_agent_callback=before_agent_callback,
    #after_agent_callback=after_agent_callback, #tutorial 9,

)

#initial_agent = SequentialAgent(
#    name="assessor_agent",
#    sub_agents=[task_giving_agent, router_agent],
#)

evaluations_runner = ParallelAgent(
    name="evaluations_runner",
    sub_agents=[clarity_evaluator, compliteness_evaluator],
)

root_agent = SequentialAgent(
    name="assessor_agent",
    sub_agents=[task_giving_agent, router_agent, evaluations_runner, result_synthesizer],
)