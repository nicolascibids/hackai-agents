import matplotlib.pyplot as plt
from scibids_lib.gcp.bigquery import bigquery_v3

# Constants
GCP_PROJECT = 'noted-victory-133614'
DATASET = 'ttd_math'
TABLE_PREFIX = 'opti_all_'
DATE_FORMAT = '%Y%m%d'
START_DATE = '20240201'
END_DATE = '20240220'

# Create BigQuery client
client = bigquery_v3.create_client(project_id=GCP_PROJECT)

# Function to generate table names for the given date range
def generate_table_names(start_date, end_date, date_format, table_prefix):
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, date_format)
    end = datetime.strptime(end_date, date_format)
    date_generated = [start + timedelta(days=x) for x in range(0, (end-start).days + 1)]

    return [table_prefix + date.strftime(date_format) for date in date_generated]

# Generate table names
table_names = generate_table_names(START_DATE, END_DATE, DATE_FORMAT, TABLE_PREFIX)

# Query to calculate the average `avg_pconv` for each table
avg_pconv_results = {}
for table_name in table_names:
    query = f"""
        SELECT
            DATE('{table_name[-8:]}') as date,
            AVG(avg_pconv) as avg_pconv
        FROM
            `{DATASET}.{table_name}`
    """
    rows = client.query(query)
    results = list(rows)
    if results:
        avg_pconv_results[results[0]['date']] = results[0]['avg_pconv']

# Sort the results by date
sorted_dates = sorted(avg_pconv_results.keys())
avg_pconv_values = [avg_pconv_results[date] for date in sorted_dates]

# Plotting the time series
plt.figure(figsize=(10, 5))
plt.plot(sorted_dates, avg_pconv_values, marker='o')
plt.title('Average pConv Evolution (Feb 1, 2024 - Feb 20, 2024)')
plt.xlabel('Date')
plt.ylabel('Average pConv')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
