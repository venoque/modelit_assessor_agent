from google.adk.agents import Agent

compliteness_evaluator = Agent (
    name = "compliteness_evaluator",
    model = "gemini-2.0-flash",
    description = "evaluates compliteness of the model", #important for multiagent solutions. Other agents will read it
    instruction= """
    You are the assessor agent that evaluates conceptual models. 
    You evaluate the compliteness of the given model.
    The model: {conceptual_model}
    """,
    #sub_agents= [opm_evaluator, uml_evaluator], #tutorial 7
    #tools = [get_benchmark_task], #tutorial 2
    #output_schema=EmailContent, #tutorial 4
    output_key="compliteness_evaluation", #tutorial 4
    #before_agent_callback=before_agent_callback,
    #after_agent_callback=after_agent_callback, #tutorial 9,

)