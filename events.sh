#!/bin/bash

current_time=$(date -u -d "+15 seconds" +"%Y-%m-%dT%H:%M:%S.%3NZ")

# Dodaj transkrypcję dla konkretnego momentu w streamie
current_time=$(date -u -d "+15 seconds" +"%Y-%m-%dT%H:%M:%S.%3NZ")
curl -X POST http://localhost:9000/api/streams/camera1/annotations/transcript \
  -H "Content-Type: application/json" \
  -d "{
    \"timestamp\": \"${current_time}\",
    \"text\": \"W tym momencie przechodzimy do omówienia algorytmów sortowania\",
    \"speaker\": \"Dr Smith\",
    \"confidence\": 0.95
  }"

current_time=$(date -u -d "+15 seconds" +"%Y-%m-%dT%H:%M:%S.%3NZ")
curl -X POST http://localhost:9000/api/streams/camera1/annotations/description \
  -H "Content-Type: application/json" \
  -d "{
    \"timestamp\": \"${current_time}\",
    \"description\": \"Trzech studentów pracuje przy komputerach w laboratorium\",
    \"confidence\": 0.88,
    \"tags\": [\"laboratory\", \"students\", \"computers\"]
  }"

# Dodaj pojedynczą ramkę
current_time=$(date -u -d "+15 seconds" +"%Y-%m-%dT%H:%M:%S.%3NZ")
curl -X POST http://localhost:9000/api/streams/camera1/annotations/bounding-box \
  -H "Content-Type: application/json" \
  -d "{
    \"timestamp\": \"${current_time}\",
    \"object\": {
      \"type\": \"person\",
      \"coordinates\": {
        \"x\": 100,
        \"y\": 150,
        \"width\": 50,
        \"height\": 120
      },
      \"confidence\": 0.95
    }
  }"

# Dodaj zdarzenie pojedyncze
curl -X POST http://localhost:9000/api/streams/camera1/annotations/event \
  -H "Content-Type: application/json" \
  -d "{
    \"timestamp\": \"${current_time}\",
    \"event_type\": \"motion_detected\",
    \"severity\": \"low\",
    \"location\": {
      \"x\": 320,
      \"y\": 240,
      \"area\": \"entrance\"
    }
  }"

# Pobierz wszystkie adnotacje dla streamu
curl -X GET http://localhost:9000/api/streams/camera1/annotations

