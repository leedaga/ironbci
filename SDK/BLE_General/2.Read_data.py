import asyncio
import sys
from bleak import BleakClient
import time

FIRST_NAME_ID = '0000fe42-8e22-4541-9d4c-21edae82ed19'
address = "00:80:E1:26:01:09"


data_test= 0x7FFFFF
data_check=0xFFFFFF


async def main(address):
    async with BleakClient(address) as client:
        event = asyncio.Event()  # Create the event inside the coroutine

        def callback(FIRST_NAME_ID, data):
            #print(data[0], data[1], data[2])
            voltage_1 = (data[0] << 16) | (data[1] << 8) | data[2]

           
            convert_voktage=voltage_1|data_test
            
            if convert_voktage==data_check:
                voltage_1_after_convert=(voltage_1-16777214)
            else:
                voltage_1_after_convert=voltage_1
            result=round(1000000*4.5*(voltage_1_after_convert/16777215),2)
            print(result)

            
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
