from buttplug.client import (ButtplugClientWebsocketConnector, ButtplugClient,
                             ButtplugClientDevice, ButtplugClientConnectorError)
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio
import argparse
import os
import datetime


# Dictionary to store devices, key is device name and value is the device object
devices = {}
def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def handle_vibrate_speed(address, speed):
    param = address.split("/")[-1]
    device_name = param.split("_")
    del device_name[0:2]
    device_name = ' '.join(device_name)
    
    for toy in devices.values():
        if toy[2] == device_name:
            dev = toy[1]
            limit = toy[3]
            if "VibrateCmd" in dev.allowed_messages.keys():
                safeSpeed = translate(speed,0,1,0,limit)
                tmmLog(f'Setting speed for {x[2]} to: {safeSpeed}')
                asyncio.create_task(dev.send_vibrate_cmd(safeSpeed))
        elif device_name.lower() == 'all':
            for x in devices.values():
                dev = x[1]
                limit = x[3]
                if "VibrateCmd" in dev.allowed_messages.keys():
                    safeSpeed = translate(speed,0,1,0,limit)
                    tmmLog(f'Setting speed for {x[2]} to: {safeSpeed}')
                    asyncio.create_task(dev.send_vibrate_cmd(safeSpeed))

def handle_limit(address, limit):
    
    param = address.split("/")[-1]
    device_name = param.split("_")
    del device_name[0:2]
    device_name = ' '.join(device_name)
    
    for toy in devices.values():
        if toy[2] == device_name:
            devices[toy[0]][3] = float(limit)
            tmmLog(f'Limits for {toy[2]} set to: {round(limit*100)}%')
        elif device_name.lower() == 'all':
            for toy in devices.values():
                devices[toy[0]][3] = float(limit)

            tmmLog(f'Limits for all toys set to: {round(limit*100)}%')

def all_messages(address, value):
    tmmLog(f'Address: {address} | Value: {value}')
dispatcher = Dispatcher()
dispatcher.map("/avatar/parameters/*_Vibrate_*", handle_vibrate_speed)
dispatcher.map("/avatar/parameters/*_Limit_*", handle_limit)
#dispatcher.map("/avatar/parameters/TMM_Bat_*", all_messages)
ip = "127.0.0.1"
port = 9001

server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())



def device_added(emitter, dev: ButtplugClientDevice):
    tmmLog("Device Added: {}".format(dev.name))
    devices[dev._index] = [dev._index,dev,dev.name,1.0]
    

def device_removed(emitter, dev: ButtplugClientDevice):
    tmmLog("Device removed: {}".format(devices[dev][2]))
    del devices[dev]
    

async def run(argPath: str, argPort: int = 12345):
    
    ifacePath = os.path.abspath(argPath)
    ifacePort = str(argPort)
    


    proc = await asyncio.create_subprocess_exec(
    ifacePath,
    '--servername',
    'Intiface Server',
    '--stayopen',
    '--wsinsecureport',
    ifacePort,
    '--with-lovense-connect',
    stdin=asyncio.subprocess.PIPE,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE)

    while True:
        buf = await proc.stdout.readline()
        
        if not buf:
            break

        line = buf.decode('ascii').rstrip()
        print(f'IntifaceCLI: {line}')

    stderr = await proc.communicate()
    

    print(f'[{main!r} exited with {proc.returncode}]')
    if stderr:
        print(f'[stderr]\n{stderr.decode()}')

async def main():
    
    asyncio.get_event_loop().create_task(run(os.path.join(os.getenv('LOCALAPPDATA'),'IntifaceDesktop/engine/IntifaceCLI.exe'),12345))
    # Set up Buttplug client
    connector = ButtplugClientWebsocketConnector("ws://127.0.0.1:12345")
    client = ButtplugClient("MyClient")
    client.device_added_handler += device_added
    client.device_removed_handler += device_removed
    try:
        await client.connect(connector)
    except ButtplugClientConnectorError as e:
        tmmLog("Could not connect to server, exiting: {}".format(e.message))
        return
    

    
    await client.start_scanning()
    
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving
    

    while True:  # Keep the script running indefinitely
        await asyncio.sleep(1)
  
    await client.stop_scanning()
    await client.disconnect()
    

def tmmLog(message):
    time = datetime.datetime.now()
    print("TMM: {} {}".format(time, message))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        tmmLog("Received exit, exiting")
        exit()

    
