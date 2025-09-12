import asyncio
from bleak import BleakScanner, BleakClient
import matplotlib.pyplot as plt
from collections import deque
import threading
import numpy as np
import time

DEVICE_NAME = "EAREEG"
FIRST_NAME_ID = '0000fe42-8e22-4541-9d4c-21edae82ed19'

buffer_size = 250
data_buffers = {f"channel_{i+1}": deque([0]*buffer_size, maxlen=buffer_size) for i in range(8)}

# -----------------
# Plot thread
# -----------------
def plot_thread():
    plt.ion()
    fig, ax = plt.subplots(8, 1, figsize=(12, 16), sharex=True)
    lines = [ax[i].plot(np.arange(buffer_size), list(data_buffers[f"channel_{i+1}"]))[0] for i in range(8)]
    ax[-1].set_xlabel("Samples")
    plt.tight_layout()
    
    while True:
        for i in range(8):
            lines[i].set_ydata(list(data_buffers[f"channel_{i+1}"]))
            mean = np.mean(list(data_buffers[f"channel_{i+1}"]))
            ax[i].set_ylim(mean - 100, mean + 100)
        fig.canvas.draw_idle()
        fig.canvas.flush_events()
        time.sleep(0.1)  # Update 10 times per second

# -----------------
# Convert 24-bit EEG sample
# -----------------
def convert_24bit(ch):
    data_test = 0x7FFFFF
    data_check = 0xFFFFFF
    voltage = ch - 16777214 if (ch | data_test) == data_check else ch
    return round(1000000 * 4.5 * (voltage / 16777215), 2)

# -----------------
# BLE callback
# -----------------
def ble_callback(sender, data):
    channels = [(data[3*i] << 16) | (data[3*i+1] << 8) | data[3*i+2] for i in range(8)]
    processed = [convert_24bit(ch) for ch in channels]
    for i, val in enumerate(processed):
        data_buffers[f"channel_{i+1}"].append(val)

# -----------------
# BLE task
# -----------------
async def ble_task():
    devices = await BleakScanner.discover()
    device = next((d for d in devices if d.name == DEVICE_NAME), None)
    if not device:
        print("Device not found")
        return
    print(f"Found {DEVICE_NAME} at {device.address}")
    
    async with BleakClient(device.address) as client:
        print("Connected")
        await client.start_notify(FIRST_NAME_ID, ble_callback)
        while True:
            await asyncio.sleep(1)

# -----------------
# Main
# -----------------
if __name__ == "__main__":
    # Start plot in a separate thread
    threading.Thread(target=plot_thread, daemon=True).start()
    # Run BLE asyncio loop in main thread (MTA)
    asyncio.run(ble_task())
