import os
import csv
import json

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import medfilt
from scipy.interpolate import interp1d
from dtw import dtw

np.set_printoptions(suppress=True)

def custom_distance(x, y):
    # Define your custom distance measure here
    # For example, you can use absolute difference
    return np.abs(x - y)
    
# Function to extract adas data from CSV file
def extract_adas_data(csv_file):
    extracted_data = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            for element in row:
                if 'json' in element:
                    element = element[6:]
                    json_data = json.loads(element)

                    json_data = json_data['frame_ID']
                    index = next(iter(json_data.keys()))
                    json_data = json_data[index]

                    if 'trackObj' in json_data:
                        json_data = json_data['trackObj']
                        
                        if 'VEHICLE' in json_data:
                            json_data = json_data['VEHICLE']

                            for obj in json_data:
                                if 'trackObj.distanceToCamera' in obj:
                                    extracted_data.append(obj['trackObj.distanceToCamera'])
                                    
    return extracted_data

# Function to extract radar data from CSV file
def extract_radar_data(csv_file):
    extracted_static_data = []
    extracted_dynamic_data = []

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        reader = list(reader)
        np_data = np.array(reader)
        np_data = np_data[:, 1:-1]

        time_stamp = np_data[:, 0]
        time_stamp = time_stamp.astype(float)

        dynamic_distance = np_data[:, 4]
        dynamic_distance = dynamic_distance.astype(float)
        static_distance = np_data[:, 2]
        static_distance = static_distance.astype(float)

        extracted_dynamic_data = dynamic_distance.tolist()
        extracted_static_data = static_distance.tolist()
        time_stamp = time_stamp.tolist()
        # print(str(time_stamp[0]))
                                    
    return extracted_dynamic_data, extracted_static_data, time_stamp

# Function to extract json data from json file
def extract_json_data(json_file):
    extracted_data = []

    with open(json_file, 'r') as file:
        json_data = json.load(file)
        json_data = json_data['frame_ID']
        for key in json_data.keys():
            local_data = json_data[key]

            if 'tailingObj' in local_data:
                local_data = local_data['tailingObj'][0]
                if local_data['tailingObj.label'] == "VEHICLE" and local_data['tailingObj.distanceToCamera'] > 0:
                    extracted_data.append(local_data['tailingObj.distanceToCamera'])   

    return extracted_data

# Example usage
adas_folder = 'csv_data'
radar_folder = 'radar_data'
json_folder = 'json_data'
file_name = 'H14_Test_5'
adas_file_list = []
radar_file_list = []
json_file_list = []
adas_data = []
radar_static_data = []
radar_dynamic_data = []
snpe_data = []
radar_time_axis = []

# Get files in folders
for file in os.listdir(adas_folder):
    if file_name in file:
        adas_file_list.append(file)
for file in os.listdir(radar_folder):
    if file_name in file:
        radar_file_list.append(file)
for file in os.listdir(json_folder):
    if file_name in file:
        json_file_list.append(file)

if len(adas_file_list) > 1:
    sorted_adas_file_list = sorted(adas_file_list, key=lambda x: int(x.split('.')[-2]))
else:
    sorted_adas_file_list = adas_file_list

if len(radar_file_list) > 1:
    sorted_radar_file_list = sorted(radar_file_list, key=lambda x: int(x.split('.')[-2]))
else:
    sorted_radar_file_list = radar_file_list


for file in sorted_adas_file_list:
    file_path = os.path.join(adas_folder, file)
    adas_data.extend(extract_adas_data(file_path))

for file in sorted_radar_file_list:
    file_path = os.path.join(radar_folder, file)
    a, b, time = extract_radar_data(file_path)
    radar_dynamic_data.extend(a)
    radar_static_data.extend(b)
    radar_time_axis.extend(time)

for file in json_file_list:
    file_path = os.path.join(json_folder, file)
    snpe_data.extend(extract_json_data(file_path))

miss_count = 5
filtered_dynamic_radar_data = [0] * len(radar_dynamic_data)
prev_data = 0

for i, data in enumerate(radar_dynamic_data):
    if data >= 0:
        filtered_dynamic_radar_data[i] = data
        prev_data = data
    else:
        found = False
        for next_data in radar_dynamic_data[i:i+miss_count]:
            if next_data >= 0:
                if prev_data >= 0:
                    filtered_dynamic_radar_data[i] = (next_data + prev_data) / 2
                    found = True
        if not found:
            prev_data = 0

filtered_static_radar_data = [0] * len(radar_static_data)
prev_data = 0

for i, data in enumerate(radar_static_data):
    if data >= 0:
        filtered_static_radar_data[i] = data
        prev_data = data
    else:
        found = False
        for next_data in radar_static_data[i:i+miss_count]:
            if next_data >= 0:
                if prev_data >= 0:
                    filtered_static_radar_data[i] = (next_data + prev_data) / 2
                    found = True
        if not found:
            prev_data = 0

merged_radar_data = [-1] * len(radar_static_data)
for i in range(len(merged_radar_data)):
    if filtered_dynamic_radar_data[i] > 0:
        merged_radar_data[i] = filtered_dynamic_radar_data[i]
    elif filtered_static_radar_data[i] > 0:
        merged_radar_data[i] = filtered_static_radar_data[i]
    
    if merged_radar_data[i] >= 50:
        merged_radar_data[i] = -1

merged_radar_data = medfilt(merged_radar_data, kernel_size=99)
# interpolated_func = interp1d(radar_time_axis, merged_radar_data, kind='linear')

downsampling_factor = int(len(merged_radar_data) / len(adas_data))
merged_radar_data = merged_radar_data[::downsampling_factor]

for i in range(1, len(snpe_data) - 1):
    if snpe_data[i - 1] == -1 and snpe_data[i + 1] == -1:
        snpe_data[i] = -1

# Processing
adas_data = adas_data
merged_radar_data = merged_radar_data
distance, _, _, alignment_path = dtw(merged_radar_data, adas_data, dist=custom_distance)
adas_merged_radar_data = merged_radar_data[alignment_path[0]]
adas_data = np.array(adas_data)
adas_data = adas_data[alignment_path[1]]

print(len(snpe_data))
distance, _, _, alignment_path = dtw(merged_radar_data, snpe_data, dist=custom_distance)
snpe_merged_radar_data = merged_radar_data[alignment_path[0]]
snpe_data = np.array(snpe_data)
snpe_data = snpe_data[alignment_path[1]]

# Metrics
accuracy = 0
for i in range(len(adas_data)):
    error = abs(adas_data[i] - adas_merged_radar_data[i])
    if adas_merged_radar_data[i] == 0:
        continue
    error_rate = error * 100 / adas_merged_radar_data[i]
    if error_rate <= 10:
        accuracy += 1

print(f"Accuracy Dashcam: {accuracy * 100 / len(adas_data)}")

accuracy = 0
for i in range(len(snpe_data)):
    error = abs(snpe_data[i] - snpe_merged_radar_data[i])
    if snpe_merged_radar_data[i] == 0:
        continue
    error_rate = error * 100 / snpe_merged_radar_data[i]
    if error_rate <= 10:
        accuracy += 1

print(f"Accuracy SNPE: {accuracy * 100 / len(snpe_data)}")

np.save(file_name + "_adas.npy", adas_data)
np.save(file_name + "_radar.npy", merged_radar_data)

# plt.plot(adas_merged_radar_data, label='Radar')
plt.plot(snpe_merged_radar_data, label='Radar')
# plt.plot(adas_data, label='ADAS')
plt.plot(snpe_data, label='SNPE SDK')
# print(np.unique(radar_dynamic_data))
# plt.plot(radar_dynamic_data)
plt.legend()
plt.grid(True)
# plt.plot(radar_static_data)

plt.xlabel('Frames')
plt.ylabel('Distance (m)')
plt.title(file_name)

plt.show()
