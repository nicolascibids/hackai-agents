import autogen
from autogen.cache import Cache
import os
import logging

from skills import big_query
from testing_agents._description import DEVELOPER, PM


# describe the task
task = """Add 1 to the number output by the previous role. If the previous number is 20, output "TERMINATE"."""
config_list = {"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]},
gpt_config = {"config_list": config_list, "cache_seed": 42}

# agents configuration
engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=gpt_config,
    system_message=task,
    description="""I am **ONLY** allowed to speak **immediately** after `Planner`, `Critic` and `Executor`.
If the last number mentioned by `Critic` is not a multiple of 5, the next speaker must be `Engineer`.
"""
)

planner = autogen.AssistantAgent(
    name="Planner",
    system_message=task,
    llm_config=gpt_config,
    description="""I am **ONLY** allowed to speak **immediately** after `User` or `Critic`.
If the last number mentioned by `Critic` is a multiple of 5, the next speaker must be `Planner`.
"""
)

executor = autogen.AssistantAgent(
    name="Executor",
    system_message=task,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("FINISH"),
    llm_config=gpt_config,
    description="""I am **ONLY** allowed to speak **immediately** after `Engineer`.
If the last number mentioned by `Engineer` is a multiple of 3, the next speaker can only be `Executor`.
"""
)

critic = autogen.AssistantAgent(
    name="Critic",
    system_message=task,
    llm_config=gpt_config,
    description="""I am **ONLY** allowed to speak **immediately** after `Engineer`.
If the last number mentioned by `Engineer` is not a multiple of 3, the next speaker can only be `Critic`.
"""
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    system_message=task,
    code_execution_config=False,
    human_input_mode="NEVER",
    llm_config=False,
    description="""
Never select me as a speaker.
"""
)

graph_dict = {}
graph_dict[user_proxy] = [planner]
graph_dict[planner] = [engineer]
graph_dict[engineer] = [critic, executor]
graph_dict[critic] = [engineer, planner]
graph_dict[executor] = [engineer]

agents = [user_proxy, engineer, planner, executor, critic]

# create the groupchat
group_chat = autogen.GroupChat(agents=agents, messages=[], max_round=25, allowed_or_disallowed_speaker_transitions=graph_dict, allow_repeat_speaker=None, speaker_transitions_type="allowed")

# create the manager
manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=gpt_config,
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
)

# initiate the task
user_proxy.initiate_chat(
    manager,
    message="1",
    clear_history=True
)