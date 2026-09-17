import os

from agents_on_k8s.agent import launch_agent

model_id = "gpt-5.6-luna"
openai_key = os.getenv("OPENAI_API_KEY")
gradio_port = int(os.getenv("GRADIO_PORT") or '5000')

def main() -> None:
    launch_agent(model_id=model_id, openai_key=openai_key, server_port=gradio_port)
