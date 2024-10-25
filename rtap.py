import asyncio
import json
import cv2
import websockets
from datetime import datetime
from aiohttp import web
import av
from fractions import Fraction

class RTAPServer:
    def __init__(self):
        self.clients = set()
        self.rtsp_url = "rtsp://localhost:8554/stream"  # Domyślny URL RTSP
        self.annotation_stream = None
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

    async def start_rtsp_processing(self):
        self.running = True
        try:
            container = av.open(self.rtsp_url)
            video_stream = container.streams.video[0]

            # Utworzenie strumienia metadanych
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

                        # Aktualizacja metadanych
                        metadata_stream["timestamp"] = datetime.now().isoformat()
                        metadata_stream["frame_number"] += 1

                        # Przykładowa detekcja ruchu (możesz dostosować do swoich potrzeb)
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

                            # Broadcast annotacji przez WebSocket
                            await self.broadcast_annotation(annotation)

                        await asyncio.sleep(0.001)  # Zapobieganie blokowaniu

                except av.error.EOFError:
                    print("End of stream reached")
                    break

        except Exception as e:
            print(f"Error processing RTSP stream: {e}")
        finally:
            self.running = False

    def detect_motion(self, frame):
        # Przykładowa implementacja detekcji ruchu
        # W rzeczywistej implementacji możesz użyć bardziej zaawansowanych metod
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # Uproszczona detekcja ruchu - możesz dostosować do swoich potrzeb
        movement_detected = np.mean(gray) > 127  # Przykładowy próg

        if movement_detected:
            return {
                "x": 0,
                "y": 0,
                "width": frame.shape[1],
                "height": frame.shape[0]
            }
        return None

    async def start_server(self, host='0.0.0.0', port=8765):
        app = web.Application()
        app.router.add_get('/ws', self.handle_websocket)

        # Uruchomienie serwera WebSocket
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        print(f"RTAP Server started on ws://{host}:{port}")

        # Uruchomienie przetwarzania RTSP
        await self.start_rtsp_processing()

# Klient RTAP do testów
class RTAPClient:
    def __init__(self, url=None, host='localhost', port=9000):
        self.url = url or f"ws://{host}:{port}/ws"

    async def connect(self):
        async with websockets.connect(self.url) as websocket:
            print(f"Connected to RTAP server at {self.url}")
            while True:
                try:
                    annotation = await websocket.recv()
                    print(f"Received annotation: {annotation}")
                except websockets.ConnectionClosed:
                    print("Connection closed")
                    break

# Przykład użycia:
#client = RTAPClient(port=9000)  # lub client = RTAPClient(url="ws://localhost:9000/ws")


# Przykład użycia
async def main():
    # Uruchomienie serwera
    server = RTAPServer()
    server_task = asyncio.create_task(server.start_server())

    # Uruchomienie klienta testowego
    client = RTAPClient()
    client_task = asyncio.create_task(client.connect())

    # Oczekiwanie na zakończenie
    await asyncio.gather(server_task, client_task)

if __name__ == "__main__":
    asyncio.run(main())