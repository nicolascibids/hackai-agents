import autogen
import os
from pathlib import Path
from typing import Iterable, Optional
import agent_description as descr

from scibids_lib.gcp import datastore
from scibids_lib.gcp.bigquery import bigquery_v3

from agent_description import *

# Idea : alert to make sure 2 source of truth (reports & impressions) are aligned

########################################################################################################################
##################################################       AGENTS       ##################################################
########################################################################################################################

config_list = (
    {"model": "gpt-4-1106-preview", "api_key": os.environ["OPENAI_API_KEY"]},
)

llm_config = {
    "cache_seed": 41,  # seed for caching and reproducibility
    "config_list": config_list,
    "temperature": 0,
}

# Agents
developer = autogen.AssistantAgent(
    name="Developer",
    description="""
        A primary developer agent that writes plans and code to solve tasks.

        I will take the task description and write a code to solve it.
        The code will be sent to the `Reviewer` for approval, I first expect a response from the `Reviewer`. 
        If the response is positive, I will consider the code approuved and send it to the `Console` for execution.
        If the response is negative, I will make the necessary changes and send it back to the `Reviewer`.
    """,
    system_message=DEFAULT_AGENT_DESCRIPTION
    + BIGQUERY_AGENT_DESCRIPTION
    + DATASTORE_AGENT_DESCRIPTION
    # + CODE_SPEC_DESCRIPTION
    # + JUNIOR_AGENT_DESCRIPTION
    + """
        I understand that I cannot execute code and that is why I will not ask to execute the code. I know that `Console` is the one to execute the code.
        Pending approval, I will keep talking to the `Reviewer`.

        I understand that my code should be sent for review, so I will not ask to save file.
    """,
    llm_config=llm_config,
)

reviewer = autogen.AssistantAgent(
    name="Reviewer",
    description="""
        A reviewer agent that reviews and approves code.
        I can speak **immediately** after `Developer` and will ONLY speak to `Developer`.
        If the code is not approved OR there is no code yet, I will send it back to the `Developer`.
    """,
    system_message=DEFAULT_AGENT_DESCRIPTION
    + BIGQUERY_AGENT_DESCRIPTION
    + DATASTORE_AGENT_DESCRIPTION
    + """
        My ONLY TASK is to review the code sent by the `Developer`. I will not ask to execute the code, since I am not the one to execute it.
        I understand that I cannot execute code and that is why I will not ask to execute the code. 
        I know that `Console` is the one to execute the code, and will send the full code to `Console` for execution if I'm satisfied in my message.
        If I do not send any code to `Console`, it means I am not satisfied with the code and I WILL send it back to the `Developer`.
        I MUST SEND THE FULL TEXT CODE TO `CONSOLE` IF I AM SATISFIED, but if I am not satisfied, I will send it back to the `Developer`.
        NEVER SEND "TERMINATE" MESSAGE
    """,
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="Console",
    description="""
        Only select me when there is a code to execute, approved by `Reviewer`, OR when the task is solved.
        A user proxy agent that executes code.
    """,
    code_execution_config={
        "last_n_messages": 1,
        "use_docker": False,
    },
    human_input_mode="TERMINATE",
    llm_config=False,
)


########################################################################################################################
##################################################       GROUP CHAT CONFIG       ##################################################
########################################################################################################################

graph_dict = {}
graph_dict[user_proxy] = [developer]
graph_dict[developer] = [reviewer]
graph_dict[reviewer] = [developer, user_proxy]

agents = [user_proxy, reviewer, developer]
group_chat = autogen.GroupChat(
    agents=agents,
    messages=[],
    max_round=25,
    allowed_or_disallowed_speaker_transitions=graph_dict,
    allow_repeat_speaker=None,
    speaker_transitions_type="allowed",
)

manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
    is_termination_msg=lambda x: x.get("content", "")
    and x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    human_input_mode="TERMINATE",
)

########################################################################################################################
##################################################       SKILLS       ##################################################
########################################################################################################################


# @user_proxy.register_for_execution()
# @developer.register_for_llm(name="run_bq_query", description="Use this function to run query on GCP Bigquery.")
def run_bq_query(query: str) -> Iterable[dict]:
    """Run a query on GCP Bigquery

    Parameters
    ----------
    query : str

    Returns
    -------
    Iterable[dict]
    """
    GCP_PROJECT = "exposition-layer"
    client = bigquery_v3.create_client(project_id=GCP_PROJECT)
    rows = client.query(query)
    return list(rows)


# @user_proxy.register_for_execution()
# @developer.register_for_llm(name="run_datastore_query", description="Use this function to run query on GCP Datastore")
def run_datastore_query(
    namespace: str, kind: str, filters: list, limit: Optional[int] = None
) -> Iterable[dict]:
    """Run a query on GCP Datastore

    Parameters
    ----------
    namespace : str
        Namespace of the datastore
    kind : str
        Kind of the datastore
    filters : list[tuple[str, str, Any]]
        Should contains tuples of (field, operator, value)
        e.g. [("field1", "=", "value1"), ("field2", ">", "value2")]

    Returns
    -------
    Iterable[dict]
    """
    GCP_PROJECT = "exposition-layer"

    # Query
    client = datastore.get_or_create_client(GCP_PROJECT, namespace)
    query = client.query(kind=kind)

    for field, operator, value in filters:
        query.add_filter(field, operator, value)

    return list(query.fetch(limit=limit))


# @user_proxy.register_for_execution()
# @developer.register_for_llm(
#     name="save_file", description="Use this function to save a file"
# )
# def save_file(file_name: str, content: str):
#     """Save a file

#     Parameters
#     ----------
#     file_name : str
#         Name of the file
#     content : str
#         Content of the file
#     """
#     path = "generated_files" / Path(file_name)
#     with open(file_name, "w") as f:
#         f.write(content)
#     return


########################################################################################################################
##################################################     EXECUTION      ##################################################
########################################################################################################################


# The developer receives a message from the user_proxy, which contains the task description
message = "I have an AB Test Campaign running, I would like to have mulitple plots to evaluate if we are winning the AB test, create a plot of the KPI value over time to compare A and B"


human = autogen.UserProxyAgent(
    name="Human",
    description="A user proxy agent that executes code.",
    code_execution_config={
        "last_n_messages": 1,
        "use_docker": False,
    },
    human_input_mode="ALWAYS",
    llm_config=False,
)

data_expert = autogen.AssistantAgent(
    name="Data Expert",
    description="A primary assistant agent that writes plans and code to solve tasks.",
    system_message=descr.DATA_EXPERT_DESCRIPTION
    + descr.KPI_EXPERT_AGENT
    + descr.REPORT_EXPERT_AGENT,
    # + descr.TRANSITION_TABLE_EXPERT_AGENT,
    llm_config={
        "cache_seed": 30,  # seed for caching and reproducibility
        "config_list": config_list,
        "temperature": 0,
    },
)

human_request_chat = human.initiate_chat(
    data_expert,
    message=message,
    summary_method="last_msg",
    summary_prompt="Give an exhaustive plan of action on what the task is, what table to query and how to solve the task. Do not add any introductory phrases. If the intended request is NOT doable, please point it out.",
    clear_history=True,
)

chat_res = user_proxy.initiate_chat(
    manager,
    message=human_request_chat.summary,
    summary_method="reflection_with_llm",
    clear_history=True,
)
# import pdb

# pdb.set_trace()
