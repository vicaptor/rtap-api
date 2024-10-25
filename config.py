from pathlib import Path
import asyncio
import cv2
import websockets
from datetime import datetime
from aiohttp import web
import numpy as np
from typing import Dict, Optional

class EnvLoader:
    def __init__(self, env_path: str = '.env'):
        self.env_path = Path(env_path)
        self.env_vars: Dict[str, str] = {}

    def load(self) -> Dict[str, str]:
        if not self.env_path.exists():
            raise FileNotFoundError(f"File {self.env_path} not found")

        with open(self.env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip("'").strip('"')
                        self.env_vars[key] = value
                    except ValueError:
                        continue
        return self.env_vars

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.env_vars.get(key, default)

class RTAPServer:
    def __init__(self):
        # Załaduj konfigurację z .env
        self.env = EnvLoader()
        try:
            self.env.load()
        except FileNotFoundError:
            print("Warning: .env file not found, using defaults")

        # Pobierz konfigurację z .env lub użyj wartości domyślnych
        self.host = self.env.get('RTAP_HOST', '0.0.0.0')
        self.port = int(self.env.get('RTAP_PORT', '8765'))
        self.rtsp_url = self.env.get('RTSP_URL', 'rtsp://localhost:8554/stream')
        self.debug = self.env.get('DEBUG', 'false').lower() == 'true'

        # Inne parametry konfiguracyjne
        self.frame_interval = float(self.env.get('FRAME_INTERVAL', '0.033'))  # ~30 FPS
        self.motion_threshold = float(self.env.get('MOTION_THRESHOLD', '127'))

        self.clients = set()
        self.running = False

    async def register_client(self, websocket):
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def broadcast_annotation(self, annotation):
        if self.clients:
            await asyncio.gather(
                *[client.send(json.dumps(annotation)) for client in self.clients]
            )

    async def handle_websocket(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await self.register_client(ws)
        return ws

    async def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        movement_detected = np.mean(gray) > self.motion_threshold

        if movement_detected:
            annotation = {
                "type": "motion_detection",
                "timestamp": datetime.now().isoformat(),
                "location": {
                    "x": 0,
                    "y": 0,
                    "width": frame.shape[1],
                    "height": frame.shape[0]
                }
            }
            await self.broadcast_annotation(annotation)

            if self.debug:
                print(f"Motion detected at {annotation['timestamp']}")

    async def start_rtsp_processing(self):
        self.running = True
        cap = cv2.VideoCapture(self.rtsp_url)

        if self.debug:
            print(f"Connecting to RTSP stream: {self.rtsp_url}")

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    if self.debug:
                        print("Failed to get frame")
                    await asyncio.sleep(1)
                    continue

                await self.process_frame(frame)
                await asyncio.sleep(self.frame_interval)

        except Exception as e:
            print(f"Error processing RTSP stream: {e}")
        finally:
            self.running = False
            cap.release()

    async def start_server(self):
        app = web.Application()
        app.router.add_get('/ws', self.handle_websocket)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()

        print(f"RTAP Server started on ws://{self.host}:{self.port}")
        if self.debug:
            print("Configuration:")
            print(f"RTSP URL: {self.rtsp_url}")
            print(f"Frame interval: {self.frame_interval}")
            print(f"Motion threshold: {self.motion_threshold}")

        await self.start_rtsp_processing()

async def main():
    server = RTAPServer()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())