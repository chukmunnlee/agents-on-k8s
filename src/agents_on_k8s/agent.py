from smolagents import CodeAgent, OpenAIServerModel, GradioUI

def launch_agent(openai_key, model_id="gpt-5.6-luna", server_port=5000, max_steps=5) -> None:

    model = OpenAIServerModel(model_id=model_id, api_key=openai_key)
    agent = CodeAgent(model=model, add_base_tools=True, tools=[], max_steps=max_steps)

    ui = GradioUI(agent=agent)
    ui.launch(server_port=server_port, server_name="0.0.0.0", share=False)
