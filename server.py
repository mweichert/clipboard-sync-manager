import argparse
import asyncio
import websockets
import json
from logger import Logger

clients = {}  # clientId: websocket
logger = Logger()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Clipboard Sync Manager Server")
    parser.add_argument('--address', type=str, default='0.0.0.0', help='Listening address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=16789, help='Listening port (default: 16789)')
    return parser.parse_args()

async def handle_registration(websocket, clientId):
    if clientId in clients:
        if not clients[clientId].open:
            logger.info(f"Client ID {clientId} re-registered with a new connection.")
        else:
            logger.info(f"Client ID {clientId} is already registered with an active connection.")
            await websocket.send(json.dumps({"event": "registration-failed", "reason": "already registered"}))
            return
    else:
        logger.info(f"Client {clientId} registered successfully.")
    
    clients[clientId] = websocket
    await websocket.send(json.dumps({"event": "registration-success", "clientId": clientId}))

async def handle_deregistration(websocket, clientId):
    if clientId in clients:
        del clients[clientId]
    await websocket.send(json.dumps({"event": "deregistration-success", "clientId": clientId}))
    logger.info(f"Client {clientId} deregistered successfully.")

async def relay_clipboard_content(clientId, content):
    for cid, ws in list(clients.items()):
        if cid != clientId:
            try:
                await ws.send(json.dumps({"event": "clipboard", "clientId": clientId, "content": content}))
                logger.info(f"Clipboard content relayed to {cid}.")
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"Connection with client {cid} closed unexpectedly. Error: {e}")
                continue
            except Exception as e:
                logger.error(f"Error relaying clipboard content to {cid}. Error: {str(e)}", exc_info=True)

async def handle_client(websocket, path):
    clientId = None  # Initialize clientId to None
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                event = data.get("event")
                clientId = data.get("clientId")

                if event == "register":
                    if not clientId:
                        await websocket.send(json.dumps({"event": "registration-failed", "clientId": "missing"}))
                        logger.warning("Registration failed due to missing clientId.")
                    else:
                        await handle_registration(websocket, clientId)

                elif event == "deregister":
                    if not clientId:
                        logger.warning("Deregistration attempt without clientId.")
                    else:
                        await handle_deregistration(websocket, clientId)

                elif event == "clipboard":
                    content = data.get("content")
                    if clientId and content:
                        await relay_clipboard_content(clientId, content)
                    else:
                        logger.warning("Clipboard event received with missing clientId or content.")
                
                elif event == "ping":
                    timestamp = data.get("timestamp")
                    if timestamp:
                        await websocket.send(json.dumps({"event": "pong", "timestamp": timestamp}))
                        logger.info(f"Pong sent in response to ping from {clientId}.")

            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON message. Error: {str(e)}", exc_info=True)
    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"Client connection closed: {e}")
        if clientId and clientId in clients:  # Check if clientId is not None and exists in clients before attempting to delete
            del clients[clientId]
            logger.info(f"Client {clientId} removed from registry due to connection closure.")
    except Exception as e:
        logger.error(f"Error handling client: {str(e)}", exc_info=True)

async def start_server(address, port):
    try:
        async with websockets.serve(handle_client, address, port, ping_interval=60, ping_timeout=30):
            logger.info(f"Server started on {address}:{port}")
            await asyncio.Future()  # Run server forever
    except Exception as e:
        logger.error(f"Failed to start server on {address}:{port}. Error: {str(e)}", exc_info=True)

def main():
    try:
        args = parse_arguments()
        address = args.address
        port = args.port

        logger.info(f"Server is configured to listen on {address}:{port}")
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(start_server(address, port))
        except KeyboardInterrupt:
            logger.info("Server shutdown initiated.")
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            list(map(lambda task: task.cancel(), tasks))
            loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            loop.close()
            logger.info("Server shutdown completed.")
    except Exception as e:
        logger.error(f"An error occurred while starting the server: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()