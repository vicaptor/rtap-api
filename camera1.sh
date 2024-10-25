#!/bin/bash

curl -X POST http://localhost:9000/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "camera1",
    "url": "rtsp://192.168.1.100:554/stream1",
    "description": "Main entrance camera"
  }'


# Lista wszystkich streamów
curl -X GET http://localhost:9000/api/streams


# Dodaj transkrypcję dla konkretnego momentu w streamie
curl -X POST http://localhost:9000/api/streams/lecture_room/annotations/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:30:15.123Z",
    "text": "W tym momencie przechodzimy do omówienia algorytmów sortowania",
    "speaker": "Dr Smith",
    "confidence": 0.95
  }'

curl -X POST http://localhost:9000/api/streams/camera1/annotations/description \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:31:00.000Z",
    "description": "Trzech studentów pracuje przy komputerach w laboratorium",
    "confidence": 0.88,
    "tags": ["laboratory", "students", "computers"]
  }'

# Dodaj pojedynczą ramkę
curl -X POST http://localhost:9000/api/streams/camera1/annotations/bounding-box \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:32:00.000Z",
    "object": {
      "type": "person",
      "coordinates": {
        "x": 100,
        "y": 150,
        "width": 50,
        "height": 120
      },
      "confidence": 0.95
    }
  }'

# Dodaj zdarzenie pojedyncze
curl -X POST http://localhost:9000/api/streams/camera1/annotations/event \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:33:00.000Z",
    "event_type": "motion_detected",
    "severity": "low",
    "location": {
      "x": 320,
      "y": 240,
      "area": "entrance"
    }
  }'

# Pobierz wszystkie adnotacje dla streamu
curl -X GET http://localhost:9000/api/streams/camera1/annotations

# Pobierz adnotacje określonego typu
curl -X GET http://localhost:9000/api/streams/camera1/annotations?type=bounding-box


# Pobierz adnotacje z zakresu czasowego
curl -X GET "http://localhost:9000/api/streams/camera1/annotations?start=2024-10-25T15:01:00.000Z&end=2024-10-25T15:04:00.000Z"

# Pobierz adnotacje z filtrowaniem
curl -X GET "http://localhost:9000/api/streams/camera1/annotations?type=event&severity=low&area=entrance"