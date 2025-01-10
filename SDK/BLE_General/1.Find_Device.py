import asyncio
from bleak import BleakScanner

async def find_eareeg():
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == "EAREEG":
            print(f"Found EAREEG device:")
            print(f"Name: {device.name}")
            print(f"Address: {device.address}")
            return device
    print("EAREEG device not found")
    return None

async def main():
    eareeg_device = await find_eareeg()
    if eareeg_device:
        # Add any additional actions you want to perform with the device here
        pass

asyncio.run(main())

