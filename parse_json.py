import os
import csv
import json

import numpy as np
import matplotlib.pyplot as plt
# from scipy.signal import medfilt
# from scipy.interpolate import interp1d
# from dtw import dtw


# Function to extract adas data from CSV file
def extract_adas_data(csv_file):
    extracted_data = []
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        print("finisg read csv file")
        for row in reader:
            for element in row:
                if 'json' in element:
                    element = element[6:]
                    json_data = json.loads(element)
                   
                    json_data = json_data['frame_ID']
                    print(f'json_data[frame_ID] = {json_data}')
                    index = next(iter(json_data.keys()))
                    print(f'index :{index}')
                    json_data = json_data[index]
        
                    if 'trackObj' in json_data:
                        json_data = json_data['trackObj']
                        # print(f'json[trackObj]= {json_data}')
                        for obj in json_data:
                            if 'trackObj.distanceToCamera' in obj:
                                extracted_data.append(obj['trackObj.distanceToCamera'])
                                    
    return extracted_data

if __name__=="__main__":
    csv_file = "./191_video-adas_2024-05-10.csv"
    ys = extract_adas_data(csv_file)
    xs = [x for x in range(len(ys))]

    plt.plot(xs, ys)
    plt.show()
    # Make sure to close the plt object once done
    plt.close()

