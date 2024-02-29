from scibids_lib.gcp.bigquery import bigquery_v3
import matplotlib.pyplot as plt

GCP_PROJECT = 'noted-victory-133614'
client = bigquery_v3.create_client(project_id=GCP_PROJECT)

# Generate the list of table suffixes based on the date range
suffixes = [f'{i:08d}' for i in range(20240201, 20240221)]

# Initialize lists to store dates and avg_pconv values
dates = []
avg_pconv_values = []

# Query each table and collect avg_pconv
for suffix in suffixes:
    table_name = f'ttd_math.opti_all_{suffix}'
    query = f"""SELECT '{suffix}' as date, AVG(avg_pconv) as avg_pconv
             FROM `{table_name}`
             GROUP BY date"""
    rows = client.query(query)
    results = list(rows)
    if results:
        dates.append(results[0]['date'])
        avg_pconv_values.append(results[0]['avg_pconv'])

# Plotting the timeseries
plt.figure(figsize=(10, 5))
plt.plot(dates, avg_pconv_values, marker='o')
plt.title('Average pConv Timeseries')
plt.xlabel('Date')
plt.ylabel('Average pConv')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('avg_pconv_timeseries.png')
plt.show()
