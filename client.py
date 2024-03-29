import asyncio
import argparse
import socket
import websockets
import json
import subprocess
import shutil
import signal
from logger import Logger
import datetime
from websockets.exceptions import ConnectionClosedError

logger = Logger()

# Global variables
websocket = None
args = None  # Global variable to store command line arguments

def parse_arguments():
    parser = argparse.ArgumentParser(description="Clipboard Sync Manager Client")
    parser.add_argument('--server', type=str, required=True, help='Server IP address. This argument is required.')
    parser.add_argument('--port', type=int, default=16789, help='Server port (default: 16789)')
    parser.add_argument('--client-id', type=str, default=socket.gethostname(), help='Client ID (default: hostname of the machine)')
    return parser.parse_args()

async def listen_for_events():
    global websocket
    try:
        async for message in websocket:
            data = json.loads(message)
            event = data.get("event")
            clientId = data.get("clientId")
            content = data.get("content")

            if event == "clipboard" and clientId and content:
                xclip_path = shutil.which('xclip')
                if not xclip_path:
                    logger.error("xclip utility is not found. Please ensure it's installed and in the system's PATH.")
                    return  # Stop listening for events if xclip is not found
                subprocess.run([xclip_path, '-selection', 'clipboard', '-in'], input=content.encode(), check=True)
                logger.info(f"Clipboard content updated: {content}")
            elif event == "pong":
                logger.info("Pong received from server.")
            else:
                # Fallback case for unrecognized event types
                logger.info(f"Received an unrecognized event type: '{event}'. Data: {data}")
    except ConnectionClosedError as e:
        logger.error(f"WebSocket connection has been closed unexpectedly. Please check the server status and try reconnecting.")
        await attempt_reconnection(args.server, args.port, args.client_id)
    except Exception as e:
        logger.error("Error listening for events.", exc_info=True)

async def attempt_reconnection(server, port, clientId):
    global websocket
    delay = 1  # Starting delay of 1 second
    max_delay = 64
    while True:
        try:
            logger.info(f"Attempting to reconnect to the server. Attempting in {delay} seconds...")
            await asyncio.sleep(delay)
            websocket = await websockets.connect(f"ws://{server}:{port}", ping_interval=30, ping_timeout=40)
            await websocket.send(json.dumps({"event": "register", "clientId": clientId}))
            response = await websocket.recv()
            response_data = json.loads(response)
            if response_data.get("event") == "registration-success":
                logger.info(f"Reconnected and registered with the server successfully as {clientId}.")
                listen_task = asyncio.create_task(listen_for_events())
                monitor_task = asyncio.create_task(monitor_clipboard(clientId))
                await asyncio.gather(listen_task, monitor_task)
                break  # Exit the loop on successful reconnection
            else:
                logger.error("Failed to register with the server during reconnection attempt.")
        except Exception as e:
            logger.error(f"Reconnection attempt failed. Will try again in {delay} seconds.", exc_info=True)
            delay = min(delay * 2, max_delay)  # Double the delay for the next attempt, max out at max_delay seconds

async def send_clipboard_content_to_server(clientId, content):
    global websocket
    if websocket and websocket.open:
        try:
            await websocket.send(json.dumps({"event": "clipboard", "clientId": clientId, "content": content}))
            logger.info(f"Clipboard content sent to server successfully. Content: {content[:30]}...")  # Log only the first 30 characters for brevity
        except Exception as e:
            logger.error("Failed to send clipboard content to server.", exc_info=True)

async def monitor_clipboard(clientId):
    global websocket
    clipcat_path = shutil.which('clipcat-notify')
    if not clipcat_path:
        logger.error("clipcat-notify utility is not found. Please ensure it's installed and in the system's PATH.")
        return

    xclip_path = shutil.which('xclip')
    if not xclip_path:
        logger.error("xclip utility is not found. Please ensure it's installed and in the system's PATH.")
        return

    previous_clipboard_content = None
    while True:
        try:
            process = await asyncio.create_subprocess_exec(clipcat_path, '--no-primary', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            output, error = await process.communicate()

            if process.returncode != 0:
                logger.error(f"clipcat-notify returned non-zero exit status: {process.returncode}.")
                continue

            try:
                process_xclip = await asyncio.create_subprocess_exec(xclip_path, '-selection', 'clipboard', '-out', stdout=asyncio.subprocess.PIPE)
                stdout, stderr = await process_xclip.communicate()
                clipboard_content = stdout.decode('utf-8')
                if clipboard_content != previous_clipboard_content:
                    previous_clipboard_content = clipboard_content
                    await send_clipboard_content_to_server(clientId, clipboard_content)
            except Exception as e:
                logger.error("Error while executing xclip.", exc_info=True)
        except Exception as e:
            logger.error("Error while executing clipcat-notify.", exc_info=True)

async def register_with_server(server, port, clientId):
    global websocket
    uri = f"ws://{server}:{port}"
    try:
        websocket = await websockets.connect(uri, ping_interval=30, ping_timeout=40)
        await websocket.send(json.dumps({"event": "register", "clientId": clientId}))
        logger.info(f"Attempting to register with the server as {clientId}.")

        response = await websocket.recv()
        response_data = json.loads(response)
        if response_data.get("event") == "registration-success":
            logger.info(f"Successfully registered with the server as {clientId}.")
            return True
        elif response_data.get("event") == "registration-failed" and response_data.get("reason") == "already registered":
            logger.info(f"Client ID {clientId} is already registered with the server. Continuing with existing registration.")
            return True
        else:
            logger.info(f"Registration with the server as {clientId} failed. Reason: {response_data.get('reason')}")
            return False
    except Exception as e:
        logger.error(f"Failed to connect to the server at {uri}. Will attempt to reconnect.", exc_info=True)
        return False

async def deregister_from_server(clientId):
    global websocket
    try:
        if websocket and websocket.open:
            await websocket.send(json.dumps({"event": "deregister", "clientId": clientId}))
            logger.info(f"Sent deregistration request for clientId {clientId}.")
    except Exception as e:
        logger.error("Failed to send deregistration request.", exc_info=True)

async def main_loop():
    global args
    registered = await register_with_server(args.server, args.port, args.client_id)
    if registered:
        try:
            listen_task = asyncio.create_task(listen_for_events())
            monitor_task = asyncio.create_task(monitor_clipboard(args.client_id))
            await asyncio.gather(listen_task, monitor_task)
            logger.info("All tasks started successfully.")
        except asyncio.CancelledError:
            logger.info("Client tasks were cancelled. Attempting to deregister and shut down cleanly.")
            await deregister_from_server(args.client_id)
            if websocket and websocket.open:
                await websocket.close()
                logger.info("WebSocket connection closed.")
            loop = asyncio.get_event_loop()
            loop.stop()

def main():
    global args
    args = parse_arguments()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def shutdown(signal, frame):
        global websocket
        logger.info("Signal received, shutting down.")
        if websocket and websocket.open:
            await deregister_from_server(args.client_id)
        loop.stop()

    for sig in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, sig), lambda s=sig: asyncio.create_task(shutdown(s, None)))

    loop.run_until_complete(main_loop())

if __name__ == "__main__":
    main()