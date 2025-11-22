.PHONY: install run test clean docs

install:
	pip install -r requirements.txt

run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	find . -type d -name "__pycache__" -exec rm -r {} +