#!/usr/bin/env -S uv run --script
# Revised Example how to control L530 smart bulb - based on original from
#     https://github.com/mihai-dinculescu/tapo/blob/main/tapo-py/examples/tapo_l530.py
# Original did not work properly - revised via screwgle AI slop

import sys,os
import asyncio
import json
from tapo import ApiClient
from tapo.requests import Color
from pprint import pprint
from tapo_discover import *

DELAY = 2  # 2
IP = "192.168.0.104"   # Driveway 2
IP = "192.168.0.105"   # West 6

class TapoL530Wrapper:

    def __init__(self, username: str, password: str, ip_address: str):
        self.client = ApiClient(username, password)
        self.ip_address = ip_address
        self.device = None

    async def connect(self):
        self.device = await self.client.l530(self.ip_address)

    async def run(self, method_name: str, *args, **kwargs):
        if self.device is None:
            await self.connect()

        try:
            method = getattr(self.device, method_name)
            return await method(*args, **kwargs)
        except Exception as e:
            if "SESSION_TIMEOUT" in str(e):
                print("Session dropped, re-authenticating...")
                await self.connect()
                method = getattr(self.device, method_name)
                return await method(*args, **kwargs)
            raise

async def main(tapo_username, tapo_password, ip_address):

    bulb = TapoL530Wrapper(tapo_username, tapo_password, ip_address)
    await bulb.connect()

    print("Turning device on...")
    await bulb.run("on")

    print("Waiting ",DELAY," seconds...")
    await asyncio.sleep(DELAY)

    print("Setting the brightness to 30%...")
    await bulb.run("set_brightness", 30)

    print("Setting the color to `Chocolate`...")
    await bulb.run("set_color", Color.Chocolate)

    print("Waiting ",DELAY," seconds...")
    await asyncio.sleep(DELAY)

    print("Setting the color to `Deep Sky Blue`...")
    await bulb.run("set_hue_saturation", 195, 100)

    print("Waiting ",DELAY," seconds...")
    await asyncio.sleep(DELAY)

    print("Setting the color to `Incandescent`...")
    await bulb.run("set_color_temperature", 2700)

    print("Waiting ",DELAY," seconds...")
    await asyncio.sleep(DELAY)

    print("Setting multiple properties in a single request...")
    try:
        await bulb.device.set().brightness(50).color(Color.HotPink).send(
            bulb.device
        )
    except Exception as e:
        if "SESSION_TIMEOUT" in str(e):
            await bulb.connect()
            await bulb.device.set().brightness(50).color(Color.HotPink).send(
                bulb.device
            )
        else:
            raise

    print("Waiting ",DELAY," seconds...")
    await asyncio.sleep(DELAY)

    print("Turning device off...")
    await bulb.run("off")

    device_info = await bulb.run("get_device_info")
    print("Device info:")
    pprint(device_info.to_dict())

    device_usage = await bulb.run("get_device_usage")
    print("Device usage:")
    pprint(device_usage.to_dict())

    
if __name__ == "__main__":
    CLOUD_USER,CLOUD_PASSWORD,IP=read_cam_rcfile("~/.camerarc")
    print(CLOUD_USER,'\t',CLOUD_PASSWORD)
    
    Devices=asyncio.run( find_tapo(CLOUD_USER,CLOUD_PASSWORD,IP) )   # "192.168.0.255") )
    print('\nDevices=',Devices)        

    Cameras,Bulbs,Plugs,Other = sort_devices(Devices)
    print('\nBulbs=',Bulbs)

    for bulb in Bulbs:
        if bulb['NAME']=='West 6':
            IP=bulb['IP']
            break
    #sys.exit(0)
    
    asyncio.run( main(CLOUD_USER,CLOUD_PASSWORD,IP) )
