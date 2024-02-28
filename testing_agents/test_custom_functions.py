import autogen
from autogen.cache import Cache
import os
import logging

from skills import big_query

config_list = ({"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},)


llm_config = {
    "config_list": config_list,
    "timeout": 120,
}
chatbot = autogen.AssistantAgent(
    name="chatbot",
    system_message="For coding tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
)

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5,
    code_execution_config={
        "work_dir": "coding",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
)


autogen.agentchat.register_function(
    big_query.run_bq_query,
    caller=chatbot,
    executor=user_proxy,
    name="run_bq_query",
    description="Use this function to query BQ tables",
)

message = """
    Can you analyse the table noted-victory-133614.ttd_math.opti_all_20240202 ? 
"""
with Cache.disk() as cache:
    # start the conversation
    user_proxy.initiate_chat(
        chatbot,
        message=message,
        cache=cache,
    )