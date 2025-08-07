import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# Load Excel file
#df = pd.read_excel('dataset.xlsx')  # First row is header
df = pd.read_csv('chew.csv') 
# Define bandpass filter parameters
fs = 250  # Sampling frequency in Hz
lowcut = 1
highcut = 20
order = 4

# Design Butterworth bandpass filter
nyq = 0.5 * fs
low = lowcut / nyq
high = highcut / nyq
b, a = butter(order, [low, high], btype='band')

# Detect number of channels automatically
num_channels = df.shape[1]  # total columns in file

plt.figure(figsize=(14, 10))

for ch in range(num_channels):
    data = df.iloc[:, ch].values  # take column directly
    filtered_data = filtfilt(b, a, data)

    # Vertical offset so channels don’t overlap
    offset = ch * 200  # adjust if amplitude is too high or low
    plt.plot(filtered_data + offset, label=f'Ch {ch+1}')

plt.xlabel('Sample Index')
plt.ylabel('Amplitude + offset')
plt.title(f'Bandpass Filtered Signals (1–40 Hz) - {num_channels} Channels')
plt.legend(loc='upper right', ncol=2)
plt.grid(True)
plt.tight_layout()
plt.show()
