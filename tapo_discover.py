#!/usr/bin/env -S uv run --script
#
# Example how to discover devices on local lan - original is from
#     https://github.com/mihai-dinculescu/tapo/blob/main/tapo-py/examples/tapo_l530.py
#
# This seems to work - errors are from routers and/or devices that Susan is admin for

import sys,os
import asyncio
from tapo import ApiClient, DeviceType, DiscoveryResult
from utils import *

async def find_tapo(tapo_username, tapo_password, IP):
    timeout_s = int(os.getenv("TAPO_DISCOVERY_TIMEOUT", 10))

    print(f"Discovering Tapo devices on target: {IP} for {timeout_s} seconds...")

    api_client = ApiClient(tapo_username, tapo_password)
    discovery = await api_client.discover_devices(IP, timeout_s)

    # NOTE: This example uses explicit pattern matching to demonstrate all
    # DiscoveryResult variants and the way in which they expose `device_info`
    # and `handler`. For a more concise approach, you can use the
    # accessor properties instead for a few common properties:
    #
    #   device_id = discovery_result.device_id
    #   nickname = discovery_result.nickname
    #   model = discovery_result.model
    #   address = discovery_result.address
    #   device_type = discovery_result.device_type

    Devices=[]
    async for discovery_result in discovery:
        try:
            discovery_result = discovery_result.get()

            match discovery_result:
                case DiscoveryResult.Light(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.Light))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Light '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.ColorLight(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.ColorLight))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Color Light '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.RgbLightStrip(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.RgbLightStrip))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found RGB Light Strip '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.RgbicLightStrip(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.RgbicLightStrip))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found RGBic Light Strip '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.Plug(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.Plug))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Plug '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.PlugEnergyMonitoring(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.PlugEnergyMonitoring))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found EM Plug '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.PowerStrip(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.PowerStrip))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Power Strip '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.PowerStripEnergyMonitoring(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.PowerStripEnergyMonitoring))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found EM Power Strip '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.Hub(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.Hub))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Hub '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.HubIr(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.HubIr))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.CameraHub(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.CameraHub))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Camera Hub '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.Camera(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.Camera))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found Camera '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.CameraPtz(device_info, handler):
                    name = name_or(device_info.nickname, str(DeviceType.CameraPtz))
                    ip, port = handler.address
                    model=device_info.model
                    print(f"Found PTZ Camera '{name}' of model '{model}' at '{ip}:{port}'.")
                case DiscoveryResult.Other(device_info, (ip, port)):
                    # If you believe that this device is already supported through one of the existing handlers, or would like to explore adding support for a currently
                    # unsupported model, please [open an issue on GitHub](https://github.com/mihai-dinculescu/tapo/issues)
                    # to start the discussion.

                    model=device_info.model
                    name = name_or(device_info.nickname or "", str(DeviceType.Other))
                    print(
                        f"Found Other device without a dedicated handler '{name}' of model '{model}' at '{ip}:{port}'."
                    )
                    
            dev={'NAME':name, 'MODEL':model, 'IP':ip, 'port':port}
            #print(dev)
            Devices.append(dev)
        except Exception as e:
            print(f"Error discovering device: {e}")

    print("\nErrors are probably from routers and/or devices that Susan is admin for\n")
    #print(Devices)        
    return Devices


def name_or(nickname: str, device_type: str) -> str:
    """Returns the device's name, or the device type when the name is empty. A
    device can have an empty name: the Tapo app doesn't show a power strip's
    own name, for example, but `set_nickname` can set it."""
    return nickname if nickname.strip() else device_type


if __name__ == "__main__":

    USER,PASSWORD,IP=read_cam_rcfile("~/.camerarc")
    print(USER,'\t',PASSWORD,'\t',IP)
    ip2=IP.split('.')
    ip2[3]='255'
    IP2=".".join(ip2)
    Devices=asyncio.run( find_tapo(USER,PASSWORD,IP2) )   # "192.168.0.255") )

    print('\nDevices=',Devices)        

    Cameras,Bulbs,Plugs,Other = sort_devices(Devices)
    print('\nCameras=',Cameras)
