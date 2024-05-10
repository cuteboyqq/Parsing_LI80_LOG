import os
import csv
import json

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import medfilt
from scipy.interpolate import interp1d
from dtw import dtw

np.set_printoptions(suppress=True)

    
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

# Example usage
adas_folder = 'RoadTest_TeraLog_0429'
file_name = 'SFD_35m_Human.log'
data = []
bin_averages = []

# Get files in folders
file = os.path.join(adas_folder, file_name)
if os.path.exists(file):
    with open(file, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if "json" in line:
            index = line.find("tailingObj.distanceToCamera")
            tailingObj = line[index:]
            tailingObj = float(tailingObj.split(",")[0].split(":")[-1])
            data.append(tailingObj)

    data = np.array(data)
    bin_counts, bin_edges = np.histogram(data, bins=np.arange(data.min(), data.max()+2))

    for i in range(len(bin_edges) - 1):
        indices = np.where((data >= bin_edges[i]) & (data < bin_edges[i+1]))[0]

        if len(indices) > 0:
            average = np.mean(data[indices])
        else:
            average = 0
        
        bin_averages.append(average)

    plt.bar(bin_edges[:-1] - 0.5, bin_counts, width=np.diff(bin_edges), align='edge', label='Bin Counts')
    plt.plot(bin_edges[:-1], bin_averages, color='red', marker='o', linestyle='-', linewidth=2, label='Bin Averages')
    plt.xlabel('Bins')
    plt.ylabel('Frequency / Average')
    plt.title('Histogram with Bin Averages')

    for x, y in zip(bin_edges[:-1], bin_averages):
        if y == 0:
            continue
        plt.annotate(f'{y:.2f}', (x, y), textcoords="offset points", xytext=(0,5), ha='center')

    plt.legend()
    plt.grid(True)
    plt.show()

    # print(data)
else:
    raise RuntimeError("File Not Found")


