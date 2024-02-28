
import autogen
from autogen import ConversableAgent, UserProxyAgent
from autogen.cache import Cache
from autogen.agentchat.contrib.capabilities.teachability import Teachability
import os

from skills import big_query

config_list = {"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},


llm_config = {"config_list": config_list, "cache_seed": 42}

# create an AssistantAgent named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={
        "cache_seed": 41,  # seed for caching and reproducibility
        "config_list": config_list,  # a list of OpenAI API configurations
        "temperature": 0,  # temperature for sampling
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)
# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    },
)


autogen.agentchat.register_function(
    big_query.run_bq_query,
    caller=assistant,
    executor=user_proxy,
    name="run_bq_query",
    description="Use this function to query BQ tables",
)

message = """
    Can you analyse the table noted-victory-133614.ttd_math.opti_all_20240202 ? 
"""
with Cache.disk() as cache:
    while True:
        mess = input(">>> ")
        # start the conversation
        user_proxy.initiate_chat(
            assistant,
            message=mess,
            cache=cache,
        )