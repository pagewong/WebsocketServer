#-*-coding: UTF-8 -*-
import asyncio
import sys
import os
import io
import datetime
# Re-open stdin with UTF-8 encoding
sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
# Re-open stdout with UTF-8 encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

try:
    import websockets
    from websockets.server import serve
except Exception as e:
    print(f"ss:sys.executable:{sys.executable}")
    grandparent_dir = os.path.dirname(os.path.dirname(sys.executable))
    site_package_path = os.path.join(grandparent_dir, 'site-packages')
    sys.path.append(site_package_path)
    import websockets
    from websockets.server import serve

connected_clients = []  # List to keep track of connected clients


def stdout_msg(msg, pre_code=0):

    pre = ''
    if pre_code == 1:
        pre = "[发送]："
    elif pre_code == 2:
        pre = "[接收]："

    sys.stdout.write(f"{pre}{msg}\n")
    sys.stdout.flush()


async def echo(websocket, path):
    connected_clients.append(websocket)  # Add the new client to the list
    try:
        async for message in websocket:
            # message = convert_gbk_to_utf8(message)
            receive_msg = f"{message}"
            send_msg = f"ok"
            stdout_msg(receive_msg, pre_code=2)
            stdout_msg(send_msg, pre_code=1)
            await websocket.send(send_msg)
    finally:
        connected_clients.remove(websocket)  # Remove client from the list when disconnected


async def handle_stdin(stop):

    loop = asyncio.get_running_loop()
    try:
        while True:
            stdout_msg(f"encoding:{sys.stdin.encoding}")
            line = await loop.run_in_executor(None, sys.stdin.readline)
            command = line.strip()
            # command = convert_gbk_to_utf8(command)

            stdout_msg(f"{command}", 1)
            if command == "close":
                stdout_msg("Received close command")
                stop.set_result(None)
                break
            else:
                stdout_msg(f"connected_clients:{connected_clients}")
                for client in connected_clients:
                    cmd = command
                    await client.send(cmd)  # Send the received message to all connected clients
    except Exception as e:
        stdout_msg(f"send msg to client error:{e}")


async def main(host, port):
    stop = asyncio.Future()

    server = await serve(echo, host, port)
    stdout_msg(f"Start websocket server. Listening {host}:{port}")
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
    if len(arg) > 2:
        kwg['host'] = arg[1]
        kwg['port'] = arg[2]
    asyncio.run(main(**kwg))

