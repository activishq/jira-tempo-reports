install:
	pip install -r requirements.txt

run:
	python app/scripts/wait_for_db.py && streamlit run app/main.py --server.port=8501
