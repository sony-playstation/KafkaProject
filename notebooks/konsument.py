import json
from kafka import KafkaConsumer
from pymongo import MongoClient


SERVER = 'broker:9092'
TOPIC  = 'lyft_station_status'

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=[SERVER],
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)


MONGO_USER = "root"
MONGO_PASS = "admin"

mongo_client = MongoClient(
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@mongo:27017/",
    authSource="admin"
)
db   = mongo_client['rta_project']
coll = db['lyft_status']

print("Real-time consumer start. Wstawiam do MongoDB…")

for msg in consumer:
    rec      = msg.value
    api_json = rec['data']
    stations = api_json.get('data', {}).get('stations', [])

    docs = [{
        'station_id':      s.get('station_id'),
        'bikes_available': s.get('num_bikes_available'),
        'docks_available': s.get('num_docks_available'),
        'last_reported':   s.get('last_reported'),
        'collected_at':    rec.get('collected_at')
    } for s in stations]

    if docs:
        coll.insert_many(docs)
        print(f"✔️  Wstawiono {len(docs)} dokumentów do MongoDB")
