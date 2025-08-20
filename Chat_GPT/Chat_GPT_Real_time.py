import pandas as pd
import openai
import asyncio
from bleak import BleakScanner, BleakClient  # For Bluetooth Low Energy (BLE) communication
import numpy as np
from collections import deque
from scipy.signal import welch  # For power spectral density calculation (EEG band power)

# ----------------------------
# 0️⃣ OpenAI API key
# ----------------------------
# ⚠️ Replace with your actual OpenAI API key. Avoid hardcoding in production!
openai.api_key = "sk-your-api-key-here"

# ----------------------------
# 1️⃣ Dataset info (context for prompt)
# ----------------------------
dataset_info = """
You are analyzing EEG alpha power data sampled at 250 Hz
from left-brain electrodes.
Emotions to predict: Scary, Sad, Funny.
"""

# ----------------------------
# 2️⃣ Few-shot examples (used to guide GPT model predictions)
# ----------------------------
few_shot_examples = """
EEG: alpha_power=0.000028 → Emotion: Scary
EEG: alpha_power=0.001195 → Emotion: Sad
EEG: alpha_power=0.001614 → Emotion: Funny
"""

# ----------------------------
# 3️⃣ OpenAI emotion predictor (based only on alpha power)
# ----------------------------
def predict_emotion_openai(alpha_power_value: float) -> str:
    """
    Uses GPT to classify EEG alpha power values into discrete emotions.
    Few-shot examples + dataset description are included in the prompt.
    """
    prompt = f"""
{dataset_info}

Here are some labeled examples:
{few_shot_examples}

Now, here is new data:
EEG: alpha_power={alpha_power_value:.6f}

Predict the emotion from only these options: Scary, Sad, Funny.
Give only the emotion word.
"""
    # Call OpenAI Chat Completions API
    response = openai.chat.completions.create(
        model="gpt-4o-mini",  # lightweight GPT-4 optimized for speed/cost
        messages=[{"role": "user", "content": prompt}],
        temperature=0  # deterministic output (no randomness)
    )
    return response.choices[0].message.content.strip()

# ----------------------------
# 4️⃣ Real-time EEG streaming (Ch1 only)
# ----------------------------

DEVICE_NAME = "EAREEG"  # Expected BLE device name
FIRST_NAME_ID = '0000fe42-8e22-4541-9d4c-21edae82ed19'  # GATT characteristic UUID for EEG data
buffer_size = 250  # Store 1 second of EEG (250 Hz sampling rate)
data_buffer = []  # Stores 1 second of channel data before processing

# 🔍 Step 1: Scan for the EEG headset
async def find_eareeg_device():
    devices = await BleakScanner.discover()
    return next((d for d in devices if d.name == DEVICE_NAME), None)

# ⚡ Step 2: Convert raw BLE bytes → microvolt values for 8 EEG channels
async def process_data(data):
    """
    Converts 24-bit raw EEG data into microvolt values.
    Data comes in 8 channels, each 3 bytes.
    """
    channels = [(data[3*i] << 16) | (data[3*i + 1] << 8) | data[3*i + 2] for i in range(8)]
    processed_channels = []
    for ch in channels:
        # Handle signed 24-bit values
        voltage = ch - 16777214 if (ch | 0x7FFFFF) == 0xFFFFFF else ch
        # Convert to microvolts (scaled by device factor 4.5)
        result = round(1000000 * 4.5 * (voltage / 16777215), 6)
        processed_channels.append(result)
    return processed_channels

# 🎚️ Step 3: Extract EEG alpha power (8–12 Hz band)
def extract_alpha(signal, fs=250):
    """
    Calculate alpha band (8–12 Hz) power from 1-second EEG signal using Welch’s PSD.
    """
    freqs, psd = welch(signal, fs=fs, nperseg=fs)
    alpha_idx = np.logical_and(freqs >= 8, freqs <= 12)
    alpha_power = np.trapz(psd[alpha_idx], freqs[alpha_idx])  # integrate PSD in alpha band
    return float(alpha_power)

# 🚀 Step 4: Main streaming loop
async def main():
    print(f"Scanning for {DEVICE_NAME}...")
    eareeg_device = await find_eareeg_device()
    if eareeg_device is None:
        print(f"{DEVICE_NAME} not found.")
        return

    print(f"Found {DEVICE_NAME} at {eareeg_device.address}")

    async with BleakClient(eareeg_device.address) as client:
        print(f"Connected to {DEVICE_NAME}")

        # BLE callback: runs every time new EEG packet arrives
        async def callback(sender, data):
            processed_channels = await process_data(data)
            ch1 = processed_channels[0]  # Use only channel 1 for analysis
            data_buffer.append(ch1)

            # Once buffer has 1 second of data → analyze
            if len(data_buffer) == buffer_size:
                alpha_power = extract_alpha(list(data_buffer))
                emotion = predict_emotion_openai(alpha_power)

                print(f"Alpha={alpha_power:.6f} → Predicted Emotion → {emotion}")
                data_buffer.clear()  # reset buffer for next second

        # Subscribe to notifications from EEG device
        await client.start_notify(FIRST_NAME_ID, callback)
        print("Streaming EEG... Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(1)  # keep loop alive
        except asyncio.CancelledError:
            pass
        finally:
            await client.stop_notify(FIRST_NAME_ID)
            print("Notification stopped.")

# Run async loop
asyncio.run(main())
