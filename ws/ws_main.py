

import asyncio
import sys

from websockets.server import serve


connected_clients = []  # List to keep track of connected clients

async def echo(websocket, path):
    connected_clients.append(websocket)  # Add the new client to the list
    try:
        async for message in websocket:
            recive_msg = f"recv:{message}"
            send_msg = f"send:ok"
            print(recive_msg)
            await websocket.send(send_msg)
    finally:
        connected_clients.remove(websocket)  # Remove client from the list when disconnected


async def handle_stdin(stop):
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        command = line.strip()
        print(f"command===:{command}")
        if command == "close":
            print("Received close command")
            stop.set_result(None)
            break
        else:
            for client in connected_clients:
                await client.send(command)  # Send the received message to all connected clients


async def main(host, port):
    stop = asyncio.Future()

    server = await serve(echo, host, port)
    print(f"Listening {host}:{port}")
    input_task = asyncio.create_task(handle_stdin(stop))

    try:
        await stop  # Wait until "close" command is received
    finally:
        server.close()
        await server.wait_closed()
        input_task.cancel()


if __name__ == '__main__':

    arg = sys.argv
    kwg = {
        'host': '0.0.0.0',
        'port': '8083'
    }
    print(f"{arg}--kwg:{kwg}")
    if len(arg) > 2:
        kwg['host'] = arg[1]
        kwg['port'] = arg[2]
    asyncio.run(main(**kwg))

