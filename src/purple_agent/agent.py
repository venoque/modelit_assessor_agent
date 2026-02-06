from google.adk.agents import Agent

from dotenv import load_dotenv
import os

load_dotenv()

root_agent = Agent (
    name = "purple_agent",
    model = "gemini-2.0-flash",
    description = "assessee agent", #important for multiagent solutions. Other agents will read it
    instruction= """
    Your role is experienced Systems Engineer.
    TASK: convert the text into Object-Process Methodology conceptual model
    """,
    #output_schema=EmailContent, #tutorial 4
    output_key="model", #tutorial 4
)