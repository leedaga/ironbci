import asyncio
import sys
from bleak import BleakClient
import time

FIRST_NAME_ID = '0000fe42-8e22-4541-9d4c-21edae82ed19'
address = "00:80:E1:26:01:09"

async def main(address):
    async with BleakClient(address) as client:
        event = asyncio.Event()  # Create the event inside the coroutine

        def callback(FIRST_NAME_ID, data):
            #print(data[0], data[1], data[2])
            rawData = (data[0] << 16) | (data[1] << 8) | data[2]
            print(rawData)
            event.set()  # Set the event when data is received

        await client.start_notify(FIRST_NAME_ID, callback)
        print("was connected")
        
        while True: 
            if not event.is_set():    
                await event.wait()  
            event.clear()
            # Add any processing you want to do after receiving data

print('address:', address)
asyncio.run(main(address))
