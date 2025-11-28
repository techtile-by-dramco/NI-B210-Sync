import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import os
import numpy as np

# Path to save the experiment data as a YAML file
current_file_path = os.path.abspath(__file__) 
current_dir = os.path.dirname(current_file_path)
parent_path = os.path.dirname(current_dir)
output_path = os.path.join(parent_path, f"data/results.csv")

df = pd.read_csv(output_path)

# Convert ts to a readable datetime index
df['ts'] = pd.to_datetime(df['ts'], format='%Y%m%d_%H%M%S')

plt.figure(figsize=(10,6))
# plt.plot(df['ts'], abs(df['CH2']), label='CH1-CH2')
# plt.plot(df['ts'], abs(df['CH3']), label='CH1-CH3')
# plt.plot(df['ts'], abs(df['CH4']), label='CH1-CH4')

plt.plot(df['ts'], df['CH2'], label='CH1-CH2')
plt.plot(df['ts'], df['CH3'], label='CH1-CH3')
plt.plot(df['ts'], df['CH4'], label='CH1-CH4')

# plt.plot(df['ts'], df['CH2']+45-360, label='CH1-CH2')
# plt.plot(df['ts'], df['CH3']+90-360, label='CH1-CH3')
# plt.plot(df['ts'], df['CH4']+135-360, label='CH1-CH4')

# print(f"CH1 - CH2 --> Mean: {np.mean(df['CH2']+45-360)} --> Std: {np.std(df['CH2']+45-360)}")
# print(f"CH1 - CH3 --> Mean: {np.mean(df['CH3']+90-360)} --> Std: {np.std(df['CH3']+90-360)}")
# print(f"CH1 - CH4 --> Mean: {np.mean(df['CH4']+135-360)} --> Std: {np.std(df['CH4']+135-360)}")

print(f"CH1 - CH2 --> Mean: {np.mean(df['CH2'])} --> Std: {np.std(df['CH2'])}")
print(f"CH1 - CH3 --> Mean: {np.mean(df['CH3'])} --> Std: {np.std(df['CH3'])}")
print(f"CH1 - CH4 --> Mean: {np.mean(df['CH4'])} --> Std: {np.std(df['CH4'])}")
         
plt.xlabel("Timestamp")
plt.ylabel("Phase (deg)")
plt.title("Phase differences relative to scope channel 1")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(parent_path + "/scope_phases.png")

# plt.show()
