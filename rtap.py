import asyncio
import json
import cv2
import numpy as np
import websockets
from datetime import datetime
from aiohttp import web
import av
from fractions import Fraction
import yaml
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print( os.getenv('RTSP_URL', "rtsp://localhost:8554/stream") )

class RTAPServer:
    def __init__(self):
        self.clients = set()
        self.rtsp_url = os.getenv('RTSP_URL', "rtsp://localhost:8554/stream")
        print( self.rtsp_url )
        self.annotation_stream = None
        self.running = False
        self.port = int(os.getenv('RTAP_PORT', 8765))
        self.host = os.getenv('RTAP_HOST', '0.0.0.0')

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}

    async def register_client(self, websocket):
        self.clients.add(websocket)
        try:
            # For aiohttp WebSocketResponse, we wait for close
            while not websocket.closed:
                await asyncio.sleep(1)
        finally:
            self.clients.remove(websocket)
            logger.info("Client disconnected")

    async def broadcast_annotation(self, annotation):
        if self.clients:
            disconnected_clients = set()
            for client in self.clients:
                try:
                    await client.send_json(annotation)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.add(client)
            
            # Remove disconnected clients
            self.clients -= disconnected_clients

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        logger.info("New client connected")
        
        try:
            await self.register_client(ws)
        except Exception as e:
            logger.error(f"Error in websocket handler: {e}")
        finally:
            return ws

    async def start_rtsp_processing(self):
        self.running = True
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                logger.info(f"Attempting to connect to RTSP stream: {self.rtsp_url}")
                container = av.open(self.rtsp_url)
                video_stream = container.streams.video[0]

                metadata_stream = {
                    "type": "metadata",
                    "timestamp": None,
                    "frame_number": 0,
                    "annotations": []
                }

                while self.running:
                    try:
                        for frame in container.decode(video=0):
                            if not self.running:
                                break

                            metadata_stream["timestamp"] = datetime.now().isoformat()
                            metadata_stream["frame_number"] += 1

                            frame_array = frame.to_ndarray(format='bgr24')
                            motion = self.detect_motion(frame_array)

                            if motion:
                                annotation = {
                                    "type": "motion_detection",
                                    "frame": metadata_stream["frame_number"],
                                    "timestamp": metadata_stream["timestamp"],
                                    "location": motion
                                }
                                metadata_stream["annotations"].append(annotation)
                                await self.broadcast_annotation(annotation)

                            await asyncio.sleep(0.001)

                    except av.error.EOFError:
                        logger.warning("End of stream reached")
                        break

            except Exception as e:
                retry_count += 1
                logger.error(f"Error processing RTSP stream (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    logger.error("Max retries reached, stopping RTSP processing")
            finally:
                self.running = False

    def detect_motion(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            movement_detected = np.mean(gray) > 127

            if movement_detected:
                return {
                    "x": 0,
                    "y": 0,
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                }
        except Exception as e:
            logger.error(f"Error in motion detection: {e}")
        return None

    async def start_server(self):
        app = web.Application()
        app.router.add_get('/ws', self.handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        try:
            await site.start()
            logger.info(f"RTAP Server started on ws://{self.host}:{self.port}")
            
            # Start RTSP processing in background
            rtsp_task = asyncio.create_task(self.start_rtsp_processing())
            
            # Keep the server running
            while True:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            await runner.cleanup()


class RTAPClient:
    def __init__(self, url=None, host='localhost', port=8765):
        self.url = url or f"ws://{host}:{port}/ws"
        self.running = True

    async def connect(self):
        retry_count = 0
        max_retries = 3

        while self.running and retry_count < max_retries:
            try:
                async with websockets.connect(self.url) as websocket:
                    logger.info(f"Connected to RTAP server at {self.url}")
                    while self.running:
                        try:
                            annotation = await websocket.recv()
                            logger.info(f"Received annotation: {annotation}")
                        except websockets.ConnectionClosed:
                            logger.warning("Connection closed")
                            break
            except Exception as e:
                retry_count += 1
                logger.error(f"Connection error (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    await asyncio.sleep(5)  # Wait before retrying
                else:
                    logger.error("Max retries reached, stopping client")
                    break


async def main():
    try:
        server = RTAPServer()
        server_task = asyncio.create_task(server.start_server())

        # Optional: Start client for testing
        if os.getenv('START_CLIENT', 'false').lower() == 'true':
            client = RTAPClient()
            client_task = asyncio.create_task(client.connect())
            await asyncio.gather(server_task, client_task)
        else:
            await server_task

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
