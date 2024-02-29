import autogen
import os
from pathlib import Path
from typing import Iterable, Optional

from scibids_lib.gcp import datastore
from scibids_lib.gcp.bigquery import bigquery_v3

import agent_description as descr

# Idea : alert to make sure 2 source of truth (reports & impressions) are aligned

########################################################################################################################
##################################################       AGENTS       ##################################################
########################################################################################################################

config_list = ({"model": "gpt-4-1106-preview", "api_key": os.environ["OPENAI_API_KEY"]},)

# Agents
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
    + descr.REPORT_EXPERT_AGENT
    + descr.TRANSITION_TABLE_EXPERT_AGENT,
    llm_config={
        "cache_seed": 41,  # seed for caching and reproducibility
        "config_list": config_list,
        "temperature": 0,
    },
)

developer = autogen.AssistantAgent(
    name="Developer",
    description="A primary assistant agent that writes plans and code to solve tasks.",
    system_message=descr.DEFAULT_AGENT_DESCRIPTION
    + descr.BIGQUERY_AGENT_DESCRIPTION
    + descr.DATASTORE_AGENT_DESCRIPTION
    + descr.KPI_EXPERT_AGENT,
    llm_config={
        "cache_seed": 41,  # seed for caching and reproducibility
        "config_list": config_list,
        "temperature": 0,
    },
)

user_proxy = autogen.UserProxyAgent(
    name="Console",
    description="A user proxy agent that executes code.",
    code_execution_config={
        "last_n_messages": 1,
        "use_docker": False,
    },
    human_input_mode="NEVER",
    llm_config=False,
)


########################################################################################################################
##################################################       SKILLS       ##################################################
########################################################################################################################


# @user_proxy.register_for_execution()
# @assistant.register_for_llm(name="run_bq_query", description="Use this function to run query on GCP Bigquery.")
def run_bq_query(query: str) -> Iterable[dict]:
    """Run a query on GCP Bigquery

    Parameters
    ----------
    query : str

    Returns
    -------
    Iterable[dict]
    """
    GCP_PROJECT = "noted-victory-133614"
    client = bigquery_v3.create_client(project_id=GCP_PROJECT)
    rows = client.query(query)
    return list(rows)


# @user_proxy.register_for_execution()
# @assistant.register_for_llm(name="run_datastore_query", description="Use this function to run query on GCP Datastore")
def run_datastore_query(namespace: str, kind: str, filters: list, limit: Optional[int] = None) -> Iterable[dict]:
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
    GCP_PROJECT = "noted-victory-133614"

    # Query
    client = datastore.get_or_create_client(GCP_PROJECT, namespace)
    query = client.query(kind=kind)

    for field, operator, value in filters:
        query.add_filter(field, operator, value)

    return list(query.fetch(limit=limit))


# @user_proxy.register_for_execution()
# @assistant.register_for_llm(name="save_file", description="Use this function to save a file")
def save_file(file_name: str, content: str):
    """Save a file

    Parameters
    ----------
    file_name : str
        Name of the file
    content : str
        Content of the file
    """
    path = "generated_files" / Path(file_name)
    with open(file_name, "w") as f:
        f.write(content)
    return


########################################################################################################################
##################################################     EXECUTION      ##################################################
########################################################################################################################


# The assistant receives a message from the user_proxy, which contains the task description
message = "I'd like to know CPM for the biggest 5 campaigns of my client ?"  # You can run query on dbm_math.p3_ratios"
# message = "Can you plot the evolution of the CPM of Diageo campaigns on the last 4 days ? (only the 5 campaigns that are spending the most)"
# message = """
#     Please write a Python script that uses a parser to get a group object field
#     and then run a query to get the number of ratios applied.
#     You can run query on dbm_math.p3_ratios

#     Once the script is done, please save it as `get_ratios.py` and run it.
# """
# message = "You have 2 functions that are registered. Can you print their code ?"
# message = (
#     "Can you tell me how many unique group object field I have for today on datastore : thetradedesk.transition_table ?"
# )

human_request_chat = human.initiate_chat(
    data_expert,
    message=message,
    summary_method="reflection_with_llm",
    summary_prompt="Summarize the user request and indicate in which tables we should check. Do not add any introductory phrases. If the intended request is NOT doable, please point it out.",
    clear_history=True,
)

developer_chat = user_proxy.initiate_chat(
    developer,
    message=human_request_chat.summary,
    summary_method="reflection_with_llm",
    summary_prompt="Summarize takeaway from the conversation. Do not add any introductory phrases. If the intended request is NOT properly addressed, please point it out.",
    clear_history=True,
)


# import pdb

# pdb.set_trace()
