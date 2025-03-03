from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain_community.vectorstores import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.documents import Document
import oracledb
from langchain_text_splitters import CharacterTextSplitter
from ScrapeReview import scrape_reviews
from UseGoogle import google_search
import time

import cohere
from pydantic import BaseModel
from typing import Optional
import json
import os

API_KEY = os.getenv('API_KEY') # get in your Cohere API key here from envoirnment variable
#API_KEY = "xjG5F5HbcF49gmKKYShwGRkndnSaJ4Gnc2HONg9m"  # fill in your Cohere API key here
co = cohere.ClientV2(API_KEY)
print('API_KEY :',{API_KEY})

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "command-r-plus-08-2024"
    instructions: str = "You are a helpful Agent"
    tool_schemas: list = []
    tools_map: dict = {}


class Response(BaseModel):
    agent: Optional[Agent]
    messages: list


def run(agent, messages):
    current_agent = agent
    num_init_messages = len(messages)
    messages = messages.copy()

    print('Starting the Agent Execution : ', current_agent.name)

    while True:

        # turn python functions into tools and save a reverse map
        # tool_schemas = [function_to_schema(tool) for tool in agent.tools]
        # tools_map = {tool.__name__: tool for tool in agent.tools}
        tool_schemas = current_agent.tool_schemas
        tools_map = current_agent.tools_map
        # print('Starting the Agent instructions : ',current_agent.instructions)

        response = co.chat(
            model=current_agent.model,
            messages=[{"role": "system", "content": current_agent.instructions}] + messages,
            max_tokens=4000,
            tools=tool_schemas or None,
        )
        message = response.message
        print(message)

        if not message.tool_calls:  # if finished handling tool calls, break
            print('tool call break')
            print(f"{current_agent.name}: Assistant Message - ", message.content)
            msg = {'role': 'assistant', 'content': message.content[0].text}
            messages.append(msg)
            break
        else:
            print('tool call continued')
            print(f"{current_agent.name}: Tool Call - ", message.tool_calls)
            msg = {'role': 'assistant', 'tool_calls': message.tool_calls, 'tool_plan': message.tool_plan}
            messages.append(msg)

        # === 2. handle tool calls ===

        for tool_call in message.tool_calls:
            result = execute_tool_call(tool_call, tools_map)
            print(f"{current_agent.name}: Tool Call Result - ", result)

            if type(result) is Agent:  # if agent transfer, update current agent
                print('if block 1')
                agent_handoff = result
                transfer_msg = (
                    f"Transferred to {current_agent.name}, Answer user query by calling appropriate tools."
                )

                result_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": transfer_msg,
                }
                messages.append(result_message)

                agent_response = run(agent_handoff, [messages[0]])
                messages.extend(agent_response.messages)
                return Response(agent=agent_handoff, messages=messages[num_init_messages:])
            else:
                print('else block 1')
                result_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }

                messages.append(result_message)

    # ==== 3. return new messages =====
    # return messages[num_init_messages:]
    return Response(agent=current_agent, messages=messages[num_init_messages:])


def execute_tool_call(tool_call, tools_map):
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    # print(f"Printing Executing The Tool Call: {name}({args})")
    # call corresponding function with provided arguments
    return tools_map[name](**args)

