import autogen
from autogen.cache import Cache
import os
import logging

from skills import big_query

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO)

# export PYTHONPATH="${PYTHONPATH}:/Users/nicolasp/Documents/hackai/"

config_list = {"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},

# create an AssistantAgent named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    system_message="""
    I am an AI assistant. I can help you with a variety of tasks. I can also execute Python code. Reply TERMINATE only when the task is done.
    """,
    llm_config={
        "cache_seed": 41,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configurations
        "temperature": 0,  # temperature for sampling
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)
# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="User",
    code_execution_config={
        "last_n_messages": 1,
        "use_docker": False,
    },
    human_input_mode="NEVER",
    description=""" Execute python code. If TERMINATE, end the conversation.""",
    llm_config=False,
)

autogen.agentchat.register_function(
    big_query.run_bq_query,
    caller=assistant,
    executor=user_proxy,
    name="run_bq_query",
    description="Use this function to query BQ tables",
)

# Can you plot the history of avg_pconv noted-victory-133614.ttd_math.opti_all_20240202 ?

# the assistant receives a message from the user_proxy, which contains the task description
message = input("\nEnter a message: \n")
with Cache.disk() as cache:
    chat_res = user_proxy.initiate_chat(
        assistant,
        message=message,
        summary_method="reflection_with_llm",
    )
    print(chat_res)