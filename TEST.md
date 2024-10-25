zestaw testów API i komend curl do zarządzania streamami RTSP i różnymi typami adnotacji.



# RTAP API Tests and CURL Commands

## 1. Zarządzanie Streamami RTSP

### Dodawanie nowego streamu RTSP
```bash
# Dodaj nowy stream
curl -X POST http://localhost:9000/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "camera1",
    "url": "rtsp://192.168.1.100:554/stream1",
    "description": "Main entrance camera"
  }'

# Dodaj stream z parametrami
curl -X POST http://localhost:9000/api/streams \
  -H "Content-Type: application/json" \
  -d '{
    "name": "lecture_room",
    "url": "rtsp://192.168.1.101:554/lecture",
    "description": "Lecture room camera",
    "parameters": {
      "fps": 30,
      "resolution": "1920x1080",
      "audio": true
    }
  }'
```

### Listowanie streamów
```bash
# Lista wszystkich streamów
curl -X GET http://localhost:9000/api/streams

# Pobierz szczegóły konkretnego streamu
curl -X GET http://localhost:9000/api/streams/camera1
```

## 2. Adnotacje Transkrypcji

### Dodawanie transkrypcji w czasie rzeczywistym
```bash
# Dodaj transkrypcję dla konkretnego momentu w streamie
curl -X POST http://localhost:9000/api/streams/lecture_room/annotations/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:30:15.123Z",
    "text": "W tym momencie przechodzimy do omówienia algorytmów sortowania",
    "speaker": "Dr Smith",
    "confidence": 0.95
  }'

# Dodaj transkrypcję z metadanymi
curl -X POST http://localhost:9000/api/streams/lecture_room/annotations/transcript \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:30:20.456Z",
    "text": "Algorytm quicksort ma złożoność O(n log n)",
    "speaker": "Dr Smith",
    "confidence": 0.92,
    "metadata": {
      "language": "pl",
      "topic": "algorithms",
      "keywords": ["sorting", "complexity"]
    }
  }'
```

## 3. Adnotacje Opisowe

### Dodawanie opisów sceny
```bash
# Dodaj opis ogólny
curl -X POST http://localhost:9000/api/streams/camera1/annotations/description \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:31:00.000Z",
    "description": "Trzech studentów pracuje przy komputerach w laboratorium",
    "confidence": 0.88,
    "tags": ["laboratory", "students", "computers"]
  }'

# Dodaj opis z lokalizacją
curl -X POST http://localhost:9000/api/streams/camera1/annotations/description \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:31:05.000Z",
    "description": "Student prezentuje projekt na tablicy interaktywnej",
    "location": {
      "x": 450,
      "y": 280,
      "area": "front_of_room"
    },
    "tags": ["presentation", "interactive_board"]
  }'
```

## 4. Adnotacje Obiektów (Bounding Boxes)

### Dodawanie ramek wokół obiektów
```bash
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

# Dodaj multiple ramki
curl -X POST http://localhost:9000/api/streams/camera1/annotations/bounding-boxes \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:32:05.000Z",
    "objects": [
      {
        "type": "person",
        "coordinates": {
          "x": 100,
          "y": 150,
          "width": 50,
          "height": 120
        },
        "confidence": 0.95,
        "label": "student_1"
      },
      {
        "type": "laptop",
        "coordinates": {
          "x": 200,
          "y": 300,
          "width": 40,
          "height": 30
        },
        "confidence": 0.88,
        "label": "device_1"
      }
    ]
  }'
```

## 5. Adnotacje Zdarzeń

### Dodawanie zdarzeń
```bash
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

# Dodaj złożone zdarzenie
curl -X POST http://localhost:9000/api/streams/camera1/annotations/event \
  -H "Content-Type: application/json" \
  -d '{
    "timestamp": "2024-03-15T14:33:05.000Z",
    "event_type": "interaction",
    "description": "Student podnosi rękę do odpowiedzi",
    "participants": ["student_id_123"],
    "location": {
      "x": 400,
      "y": 300,
      "area": "middle_row"
    },
    "metadata": {
      "duration": 5.2,
      "confidence": 0.87,
      "related_events": ["question_asked"]
    }
  }'
```

## 6. Zapytania o Adnotacje

### Pobieranie adnotacji
```bash
# Pobierz wszystkie adnotacje dla streamu
curl -X GET http://localhost:9000/api/streams/camera1/annotations

# Pobierz adnotacje określonego typu
curl -X GET http://localhost:9000/api/streams/camera1/annotations?type=bounding-box

# Pobierz adnotacje z zakresu czasowego
curl -X GET "http://localhost:9000/api/streams/camera1/annotations?start=2024-10-25T15:01:00.000Z&end=2024-10-25T15:04:00.000Z"

# Pobierz adnotacje z filtrowaniem
curl -X GET "http://localhost:9000/api/streams/camera1/annotations?type=event&severity=low&area=entrance"
```

## 7. WebSocket Subscribe

### Subskrypcja real-time adnotacji
```bash
# Za pomocą wscat (należy zainstalować: npm install -g wscat)
wscat -c ws://localhost:9000/api/streams/camera1/annotations/ws

# Subskrypcja z parametrami (przez URL)
wscat -c "ws://localhost:9000/api/streams/camera1/annotations/ws?types=transcript,event"
```

## Przykłady użycia w skrypcie testowym



Aby użyć tych testów:

1. Zapisz komendy curl jako skrypty:
```bash
mkdir rtap-tests
cd rtap-tests
# Skopiuj zawartość artefaktu do plików .sh
chmod +x *.sh
```

2. Uruchom testy:
```bash
./test_annotations.sh
```

3. Monitoruj WebSocket:
```bash
npm install -g wscat
wscat -c ws://localhost:9000/api/streams/camera1/annotations/ws
```

Dodatkowe sugestie:
1. Dodaj walidację odpowiedzi API
2. Dodaj testy wydajności dla wielu równoczesnych adnotacji
3. Zaimplementuj testy długoterminowej stabilności
4. Dodaj testy dla różnych formatów danych wejściowych

Czy chciałbyś, żebym:
1. Rozwinął któryś z typów adnotacji?
2. Dodał więcej przykładów testów?
3. Stworzył skrypt do automatycznego testowania wszystkich endpointów?