# README.md

## Uruchomienie

1. W katalogu projektu:

   ```bash
   docker-compose up -d
   ```
2. Otwórz JupyterLab: [http://localhost:8888](http://localhost:8888) (token: `root`)

## Producer

W terminalu JupyterLab:

```bash
cd ~/notebooks
python3 GBFS_producer.py
```

Publikuje co 60 s dane do Kafka topic `lyft_station_status`.

## Consumer

W osobnym terminalu JupyterLab:

```bash
cd ~/notebooks
python3 konsument.py
```

Subskrybuje topic i dopisuje rekordy do MongoDB `rta_project.lyft_status`.

## Analiza

W JupyterLab otwórz `notebooks/analysis.ipynb` i uruchom komórkę:

```python
from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb://root:admin@mongo:27017/", authSource="admin")
coll = client['rta_project']['lyft_status']
df = pd.DataFrame(list(coll.find().sort('_id', -1).limit(10)))
print(df)
```

## MongoDB

* Host: `mongo`, port: `27017`
* Użytkownik: `root`, hasło: `admin`
* Kolekcja: `rta_project.lyft_status` (append-only)
