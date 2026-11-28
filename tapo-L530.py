#!/usr/bin/env -S uv run --script
# Example how to control L530 smart bulb - original is from
#     https://github.com/mihai-dinculescu/tapo/blob/main/tapo-py/examples/tapo_l530.py
#
# This original code doesn't quite work right - see revised code in taop-L530-a.py

import sys,os
import asyncio
import json
from tapo import ApiClient
from tapo.requests import Color

async def main():
    #tapo_username, tapo_password, ip_address = require_env_vars(
    #    "TAPO_USERNAME", "TAPO_PASSWORD", "IP_ADDRESS"
    #)
    tapo_username = USER
    tapo_password = PASSWORD
    ip_address    = "192.168.0.104"

    client = ApiClient(tapo_username, tapo_password)
    device = await client.l530(ip_address)

    print("Turning device on...")
    await device.on()

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Setting the brightness to 30%...")
    await device.set_brightness(30)

    print("Setting the color to `Chocolate`...")
    await device.set_color(Color.Chocolate)

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Setting the color to `Deep Sky Blue` using the `hue` and `saturation`...")
    await device.set_hue_saturation(195, 100)

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Setting the color to `Incandescent` using the `color temperature`...")
    await device.set_color_temperature(2700)

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Using the `set` API to set multiple properties in a single request...")
    await device.set().brightness(50).color(Color.HotPink).send(device)

    print("Waiting 2 seconds...")
    await asyncio.sleep(2)

    print("Turning device off...")
    await device.off()

    device_info = await device.get_device_info()
    print(f"Device info: {device_info.to_dict()}")

    device_usage = await device.get_device_usage()
    print(f"Device usage: {device_usage.to_dict()}")


if __name__ == "__main__":
    rcfile=os.path.expanduser("~/.camerarc")
    with open(rcfile) as json_data_file:
        cams = json.load(json_data_file)
    SETTINGS = cams[0]
    print(SETTINGS)
    USER     = SETTINGS['CLOUD_USER']
    PASSWORD = SETTINGS['CLOUD_PASSWORD']
    print(USER,'\t',PASSWORD)
    #sys.exit(0)
    
    asyncio.run(main())
