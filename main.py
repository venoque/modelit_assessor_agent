import uuid
from dotenv import load_dotenv
import os
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from src.assessor_agent import root_agent as assessor_agent
from utils import call_agent_async

load_dotenv()

# Create a new session service to store state
session_service = InMemorySessionService()

#initial_state = {
#    "row_index": 0,
#}

async def main_async():
    # Create a NEW session
    APP_NAME = "Assessor Agent"
    USER_ID = "Purple Agent"
    SESSION_ID = str(uuid.uuid4())
    stateful_session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        #state=initial_state,
    )

    print("CREATED NEW SESSION:")
    print(f"\tSession ID: {SESSION_ID}")

    runner = Runner(
        agent=assessor_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ===== PART 5: Interactive Conversation Loop =====
    print("\nWelcome")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    while True:
        # Get user input
        user_input = input("Model: ")

        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit"]:
            print("Ending conversation. Your data has been saved to the database.")
            break

        # Process the user query through the agent
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main_async())