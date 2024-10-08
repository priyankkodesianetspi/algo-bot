import logging as logger

from src.llm._types import Message, Role
from src.llm.models import agent_setup


def process_chat(prompt):
    chat = agent_setup(agent_model="gpt-4o", agent_temp=1.0, agent_top_p=0.9, agent_max_tokens=10000)

    logger.info(f"Chat object type: {type(chat)}")
    logger.info(f"Chat object methods: {dir(chat)}")

    # Create the chat messages list
    messages = [# Uncomment and customize the system prompt if needed
        # Message(role=Role.system, content="system_prompt"),
        Message(role=Role.user, content=prompt), ]

    # Process the chat and return the response content
    response = chat(messages)
    return response.content
