#!/usr/bin/env python3

import asyncio
import websockets
import json
import argparse
import aioconsole

async def send_message(websocket):
    while True:
        try:
            message = await aioconsole.ainput("Enter message to send (or 'quit' to exit): ")
            if message.lower() == 'quit':
                break

            try:
                # Try to parse as JSON
                json_data = json.loads(message)
                await websocket.send(json.dumps(json_data))
            except json.JSONDecodeError:
                # Send as raw text if not JSON
                await websocket.send(message)

        except Exception as e:
            print(f"Error sending message: {e}")
            break

async def receive_messages(websocket):
    while True:
        try:
            message = await websocket.recv()
            try:
                # Try to parse and pretty print JSON
                data = json.loads(message)
                print("\nReceived message:")
                print(json.dumps(data, indent=2))
            except json.JSONDecodeError:
                # Print raw message if not JSON
                print("\nReceived raw message:")
                print(message)
        except websockets.ConnectionClosed:
            print("Connection closed")
            break
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

async def websocket_client(url):
    try:
        async with websockets.connect(url) as websocket:
            print(f"Connected to {url}")

            # Create tasks for sending and receiving messages
            receive_task = asyncio.create_task(receive_messages(websocket))
            send_task = asyncio.create_task(send_message(websocket))

            # Wait for either task to complete
            await asyncio.gather(receive_task, send_task)

    except Exception as e:
        print(f"Connection failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='Interactive WebSocket client')
    parser.add_argument('--url',
                      default='ws://localhost:9000/api/streams/camera1/annotations/ws',
                      help='WebSocket URL to connect to')
    args = parser.parse_args()

    print(f"Connecting to {args.url}...")
    asyncio.get_event_loop().run_until_complete(websocket_client(args.url))

if __name__ == "__main__":
    main()