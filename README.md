python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip list
python ./download_nltk.py
python ./script/build_vectordb.py
(python ./script/manage_db.py list/reset)
python ./script/import_mbfc_data.py