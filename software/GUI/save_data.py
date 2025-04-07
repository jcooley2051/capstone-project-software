import csv
from datetime import datetime, timedelta

INPUT_FILE = '/home/admin/Documents/capstone-project-software/software/measurements.csv'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

# Read the data from CSV
with open(INPUT_FILE, 'r', newline='') as infile:
    reader = list(csv.DictReader(infile))

# Get the most recent timestamp
latest_time = max(datetime.strptime(row['Timestamp'], TIME_FORMAT) for row in reader)

# Compute the cutoff time (5 minutes before latest)
cutoff_time = latest_time - timedelta(minutes=5)

# Filter the rows within the last 5 minutes
filtered_rows = [row for row in reader if datetime.strptime(row['Timestamp'], TIME_FORMAT) >= cutoff_time]

# Generate output filename with timestamp
timestamp_str = latest_time.strftime('%Y%m%d_%H%M%S')
output_file = f'saved_data_{timestamp_str}.csv'

# Save the filtered rows to a new CSV
if filtered_rows:
    with open(output_file, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=filtered_rows[0].keys())
        writer.writeheader()
        writer.writerows(filtered_rows)
    print(f"Saved {len(filtered_rows)} rows to {output_file}")
else:
    print("No data found in the last 5 minutes.")
