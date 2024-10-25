#!/bin/bash

# Test dodawania streamu i różnych typów adnotacji
function test_annotations() {
    echo "Testing RTAP API..."

    # 1. Dodaj stream
    curl -X POST http://localhost:8080/api/streams \
        -H "Content-Type: application/json" \
        -d '{
            "name": "test_stream",
            "url": "rtsp://localhost:8554/test",
            "description": "Test stream"
        }'

    # 2. Dodaj transkrypcję
    curl -X POST http://localhost:8080/api/streams/test_stream/annotations/transcript \
        -H "Content-Type: application/json" \
        -d '{
            "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'",
            "text": "Test transcription",
            "speaker": "Tester"
        }'

    # 3. Dodaj bounding box
    curl -X POST http://localhost:8080/api/streams/test_stream/annotations/bounding-box \
        -H "Content-Type: application/json" \
        -d '{
            "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")'",
            "object": {
                "type": "person",
                "coordinates": {
                    "x": 100,
                    "y": 100,
                    "width": 50,
                    "height": 100
                }
            }
        }'

    # 4. Sprawdź dodane adnotacje
    curl -X GET http://localhost:8080/api/streams/test_stream/annotations

    echo "Test completed."
}

# Uruchom testy
test_annotations