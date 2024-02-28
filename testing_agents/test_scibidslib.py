
# filename: plot_histogram.py  
from scibids_lib.gcp.bigquery import bigquery_v3

def run_bq_query(query: str):
    client = bigquery_v3.create_client(project_id="noted-victory-133614")
    rows = client.query(query)
    return rows
import matplotlib.pyplot as plt  
  
# Query to extract the values for the histogram  
query = """  
SELECT metric.value AS execution_time  
FROM `noted-victory-133614.ttd_math.metrics`,  
UNNEST(metric) as metric  
WHERE metric.label = 'time_execution.main_dsp_translation.main'  
"""  
  
# Run the query  
rows = run_bq_query(query)  
  
# Extract the execution times and convert them to float  
execution_times = [float(row['execution_time']) for row in rows]  
  
# Plot the histogram  
plt.hist(execution_times, bins=30)  
plt.title('Histogram of time_execution.main_dsp_translation.main')  
plt.xlabel('Execution Time')  
plt.ylabel('Frequency')  
plt.show()  