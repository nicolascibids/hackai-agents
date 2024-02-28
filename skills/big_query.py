from scibids_lib.gcp.bigquery import bigquery_v3

def run_bq_query(query: str) -> list[dict]:
    client = bigquery_v3.create_client(project_id="noted-victory-133614")
    rows = client.query(query)
    return [row for row in rows]