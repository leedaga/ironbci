import asyncio
from bleak import BleakScanner, BleakClient
import matplotlib.pyplot as plt

DEVICE_NAME = "EAREEG"
FIRST_NAME_ID = "0000fe42-8e22-4541-9d4c-21edae82ed19"

data_for_graph = []
axis_x = 0
step = 5

async def find_eareeg_device():
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == DEVICE_NAME:
            return device
    return None

async def main():
    device = await find_eareeg_device()
    if device is None:
        print(f"{DEVICE_NAME} not found")
        return

    print(f"Found {DEVICE_NAME} at {device.address}")
    async with BleakClient(device.address) as client:
        print("Connected!")

        def callback(sender, data):
            global data_for_graph, axis_x
            data_result = 0
            data_check = 0xFFFFFF
            data_test  = 0x7FFFFF

            for a_count in range(1, 19):                
                data_read = data[a_count]
                data_result = (data_result << 8) | data_read
                
                if a_count % 3 == 0: 
                    convert_data = data_result | data_test                
                    if convert_data == data_check:
                        result = (16777214 - data_result) 
                    else:      
                        result = data_result
                    result = round(1000000 * 4.5 * (result / 16777215), 2)

                    data_for_graph.append(result)
                    
                    if len(data_for_graph) == step:
                        plt.plot(
                            range(axis_x, axis_x + step), 
                            data_for_graph, 
                            color='#0a0b0c'
                        )
                        plt.axis([
                            axis_x - 500, axis_x + 2000,
                            data_for_graph[0] - 100, data_for_graph[0] + 100
                        ])
                        axis_x += step
                        data_for_graph = []
                        plt.pause(0.001)
                        plt.draw()

                    data_result = 0
                    convert_data = 0

        await client.start_notify(FIRST_NAME_ID, callback)
        print("Notification started. Press Ctrl+C to stop.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            await client.stop_notify(FIRST_NAME_ID)
            print("Notification stopped.")

asyncio.run(main())
