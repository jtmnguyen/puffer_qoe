import os
import pandas as pd

# Define the paths
csv_file_path = os.path.expanduser("~/concatenatedUserBehaviour.csv")
pcap_dir_path = "/mnt/md0/jaber/incomingGroupedPcap/"

# Read the CSV file
df = pd.read_csv(csv_file_path)

# Get the list of directory names in the specified location
pcap_directories = set(os.listdir(pcap_dir_path))

# Filter the DataFrame to keep only the entries where the IP address matches a directory name
df_filtered = df[df['UserIP'].isin(pcap_directories)]

# Save the filtered DataFrame back to the CSV file
df_filtered.to_csv(csv_file_path, index=False)

print(f"Filtered CSV file saved at {csv_file_path}.")
