from scibids_lib.gcp.bigquery import bigquery_v3
import matplotlib.pyplot as plt

GCP_PROJECT = 'noted-victory-133614'
client = bigquery_v3.create_client(project_id=GCP_PROJECT)

# Define the date range
start_date = 20240206
end_date = 20240220

# Initialize a dictionary to store results
avg_pconv_results = {}

# Loop through the date range and perform queries
for single_date in range(start_date, end_date + 1):
    table_name = f'ttd_math.opti_all_{single_date}'
    query = f"""SELECT
                DATE('{single_date}') as date,
                AVG(avg_pconv) as avg_pconv
            FROM
                `{table_name}`
            """
    rows = client.query(query)
    results = list(rows)
    if results:
        avg_pconv_results[str(single_date)] = results[0]['avg_pconv']

# Plotting the timeserie
dates = list(avg_pconv_results.keys())
avg_pconvs = list(avg_pconv_results.values())

plt.figure(figsize=(10, 5))
plt.plot(dates, avg_pconvs, marker='o')
plt.title('Average pConv Timeserie')
plt.xlabel('Date')
plt.ylabel('Average pConv')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('avg_pconv_timeserie.png')
plt.show()
