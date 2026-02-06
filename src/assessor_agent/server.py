import argparse
import uvicorn

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

from .executor import Executor
from .agent import root_agent as assessor_agent
from google.adk.runners import Runner

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    #TODO
    #parser = argparse.ArgumentParser(description="Run the A2A agent.")
    #parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server")
    #parser.add_argument("--port", type=int, default=9009, help="Port to bind the server")
    #parser.add_argument("--card-url", type=str, help="URL to advertise in the agent card")
    #args = parser.parse_args()
    host = "localhost"
    port = 9009

    # Fill in your agent card
    # See: https://a2a-protocol.org/latest/tutorials/python/3-agent-skills-and-card/
    
    # TODO do I have more than one skill?
    skill = AgentSkill(
        id = "assessing",
        name = "Assessing",
        description = "Gives a piece of text to be transformed, wait for the conceptual model to be evaluated, evaluates the model",
        tags = ["text"],
        example = ["Agent handles Process"],
    )

    agent_card = AgentCard(
        name="Assessor Agent",
        description="""The Agent evaluates how other agents generate conceptual models.
                    It gives the task the contains the text to the assessee agent from the benchmark dataset and evaluates the response,
                    which is generated conceptual model.""",
        #url= f"http://{args.host}:{args.port}/",
        url="http://localhost:9009/",
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill]
    )


    runner = Runner(
        agent=assessor_agent,
        app_name=agent_card.name,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
        memory_service=InMemoryMemoryService(),
    )


    request_handler = DefaultRequestHandler(
        agent_executor=Executor(runner),
        task_store=InMemoryTaskStore(),
    )
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
   #uvicorn.run(server.build(), host=args.host, port=args.port)
    uvicorn.run(server.build(), host=host, port=port)


if __name__ == '__main__':
    main()
