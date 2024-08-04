import sys
import serial
import time
import numpy as np
sys.path.append("C:\\REPOS\\BackLic\\myenv\\Lib\\site-packages")
import heartpy as hp
from scipy.signal import medfilt
import matplotlib.pyplot as plt
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate('./fitapp-admin-sdk.json')
firebase_admin.initialize_app(cred, {
    'databaseURL' : 'https://fitapp-fe1fb-default-rtdb.firebaseio.com'
})

ref = db.reference("/bpm")


# Serial port setup
ser = serial.Serial('COM3', 9600, timeout=1)  # Replace 'COM3' with your port, and set a timeout
time.sleep(2)  # Allow time for the connection to establish

sampling_rate = 100  # Samples per second
window_size = 300  # Size of the window for real-time display (e.g., 3 seconds of data)
data_buffer = []  # Buffer for the pulse data

def calculate_bpm_with_heartpy(sensor_data, sampling_rate):
    try:
        # Ensure the data is a numpy array of floats
        sensor_data = np.array(sensor_data, dtype=float)
        working_data, measures = hp.process(sensor_data, sample_rate=sampling_rate, bpmmin=40, bpmmax=180)
        bpm = measures['bpm']
        return bpm
    except Exception as e:
        print(f"HeartPy processing error: {e}")
        return float('nan')

def preprocess_data(data):
    # Apply a median filter to remove noise
    filtered_data = medfilt(data, kernel_size=3)
    # Scale the data if necessary (e.g., normalization)
    min_val = np.min(filtered_data)
    max_val = np.max(filtered_data)
    if max_val > min_val:
        scaled_data = (filtered_data - min_val) / (max_val - min_val)
    else:
        scaled_data = filtered_data  # If all values are the same, scaling is not possible
    return scaled_data

# Plotting setup
plt.ion()  # Turn on interactive mode
fig, ax = plt.subplots(figsize=(12, 6))

# Initial empty plot
line, = ax.plot([], [], lw=2)
ax.set_xlim(0, window_size)
ax.set_ylim(0, 1023)  # Adjust based on expected sensor range
ax.set_title("Real-time Pulse Data")
ax.set_xlabel("Sample")
ax.set_ylabel("Amplitude")

# Function to update the plot
def update_plot(data):
    line.set_xdata(np.arange(len(data)))
    line.set_ydata(data)
    ax.set_xlim(max(0, len(data) - window_size), len(data))
    
    # Dynamically adjust the y-axis limits based on the data
    min_val = min(data)
    max_val = max(data)
    ax.set_ylim(min_val - 10, max_val + 10)  # Add some padding for better visualization

    plt.draw()
    plt.pause(0.01)




while True:
    if ser.in_waiting > 0:
        try:
            line_data = ser.readline().decode('utf-8').strip()
            print(f"Received data: {line_data}")  # Debugging: print received data
            sensor_value = int(line_data)
            data_buffer.append(sensor_value)

            # Update plot with new data
            if len(data_buffer) > window_size:
                # Maintain only the latest window_size samples
                data_buffer = data_buffer[-window_size:]

            update_plot(data_buffer)

            if len(data_buffer) >= window_size:
                # Process the latest window_size samples
                data_array = np.array(data_buffer[-window_size:], dtype=float)

                # Preprocess the data
                preprocessed_data = preprocess_data(data_array)

                # Process the batch with HeartPy
                bpm = calculate_bpm_with_heartpy(preprocessed_data, sampling_rate) 
                print(f"BPM: {bpm}")
                # Post the BPM value to Firebase
                ref.set(round(bpm))
            
        except ValueError:
            print("Received non-integer data")  # Debugging: handle non-integer data
        except KeyboardInterrupt:
            print("Interrupted by user")
            break
    else:
        print("No data available, waiting...")  # Debugging: indicate waiting state
        time.sleep(1)  # Pause for a second before checking again



