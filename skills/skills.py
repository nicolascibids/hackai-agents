from typing import Literal, Any, Iterable, Optional

from scibids_lib.gcp import datastore
from scibids_lib.config import context, config_DSP
from scibids_lib.gcp.bigquery import bigquery_v3

GCP_PROJECT = "noted-victory-133614"


def run_bq_query(query: str) -> Iterable[dict]:
    """Run a query on GCP Bigquery

    Parameters
    ----------
    query : str

    Returns
    -------
    Iterable[dict]
    """
    client = bigquery_v3.create_client(project_id=GCP_PROJECT)
    rows = client.query(query)
    return list(rows)


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
    # Query
    client = datastore.get_or_create_client(GCP_PROJECT, namespace)
    query = client.query(kind=kind)

    for field, operator, value in filters:
        query.add_filter(field, operator, value)

    return list(query.fetch(limit=limit))


if __name__ == "__main__":
    # Test for BQ
    query = "SELECT COUNT(*) AS count FROM noted-victory-133614.dbm_math.p3_ratios"
    rows = run_bq_query(query)
    print(list(rows))
    print()

    # Test for datastore
    namespace = "thetradedesk"
    kind = "transition_table"
    filters = [("day_tz", "=", 20240228), ("client_id", "=", "cbcvsmp"), ("execution_mode", "=", "daily")]
    rows = list(run_datastore_query(namespace, kind, filters, limit=3))
    print(rows)
