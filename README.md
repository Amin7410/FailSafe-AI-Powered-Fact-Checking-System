How to set up:
docker compose build --no-cache
docker compose up -d
docker exec failsafe_worker python scripts/build_stylometry_corpus.py
docker exec failsafe_worker python scripts/import_mbfc_data.py
docker exec failsafe_worker python scripts/build_vectordb.py

How to run:
docker compose logs -f