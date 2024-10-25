#!/usr/bin/env python3

import asyncio
import websockets
import json
import argparse

async def connect_websocket(url):
    try:
        async with websockets.connect(url) as websocket:
            print(f"Connected to {url}")

            # Handle incoming messages
            while True:
                try:
                    message = await websocket.recv()
                    try:
                        # Try to parse JSON and pretty print
                        data = json.loads(message)
                        print("\nReceived message:")
                        print(json.dumps(data, indent=2))
                    except json.JSONDecodeError:
                        # If not JSON, print raw message
                        print("\nReceived raw message:")
                        print(message)
                except websockets.ConnectionClosed:
                    print("Connection closed")
                    break
                except Exception as e:
                    print(f"Error: {e}")
                    break
    except Exception as e:
        print(f"Connection failed: {e}")

def main():
    parser = argparse.ArgumentParser(description='WebSocket client for testing')
    parser.add_argument('--url', default='ws://localhost:9000/api/streams/camera1/annotations/ws',
                      help='WebSocket URL to connect to')
    args = parser.parse_args()

    print(f"Connecting to {args.url}...")
    asyncio.get_event_loop().run_until_complete(connect_websocket(args.url))

if __name__ == "__main__":
    main()