.PHONY: install test lint run api docker

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

run:
	streamlit run app.py

api:
	uvicorn api:app --reload

docker:
	docker compose up --build
