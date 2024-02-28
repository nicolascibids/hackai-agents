import autogen
from autogen.cache import Cache
import os
import logging

from skills import big_query
from testing_agents._description import DEVELOPER, PM

config_list = {"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},


llm_config = {"config_list": config_list, "cache_seed": 42}
user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="Can execute python code.",
    code_execution_config={
        "last_n_messages": 5,
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    human_input_mode="TERMINATE",
)
coder = autogen.AssistantAgent(
    name="PythonDeveloper",
    system_message=DEVELOPER,
    llm_config=llm_config,
)
data_manager = autogen.AssistantAgent(
    name="DataManager",
    system_message="In charge of data management: knows how to query BQ tables. Can ask coder for help.",
    llm_config=llm_config,
)

autogen.agentchat.register_function(
    big_query.run_bq_query,
    caller=coder,
    executor=user_proxy,
    name="run_bq_query",
    description="Use this function to query BQ tables",
)

groupchat = autogen.GroupChat(agents=[user_proxy, coder, data_manager], messages=[], max_round=12)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

message = "Can you give me some insights on the table noted-victory-133614.ttd_math.opti_all_20240202 ?"
user_proxy.initiate_chat(
    manager, message=message
)