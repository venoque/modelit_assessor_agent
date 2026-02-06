from google.adk.agents import Agent
from pydantic import BaseModel

#TODO Output class

result_synthesizer = Agent (
    name = "result_synthesizer",
    model = "gemini-2.0-flash",
    description = "synthesize the results of the evaluation", #important for multiagent solutions. Other agents will read it
    instruction= """
    You synthesize the results of the evaluation.
    Clarity evaluation: {clarity_evaluation}
    Completeness evaluation: {completeness_evaluation}
    """,
    #sub_agents= [opm_evaluator, uml_evaluator], #tutorial 7
    #tools = [get_benchmark_task], #tutorial 2
    #output_schema=EmailContent, #tutorial 4
    output_key="final_evaluation", #tutorial 4
    #before_agent_callback=before_agent_callback,
    #after_agent_callback=after_agent_callback, #tutorial 9,

)