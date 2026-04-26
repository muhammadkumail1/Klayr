.PHONY: install dev test lint run docker-up docker-down migrate

install:
	pip install -r requirements.txt

dev:
	PYTHONPATH=src uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

test:
	PYTHONPATH=src pytest tests/ -v

test-domain:
	PYTHONPATH=src pytest tests/domain/ -v

lint:
	PYTHONPATH=src python -m py_compile src/domain/entities/experiment.py \
		src/domain/pipeline/graph.py \
		src/api/main.py

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

migrate:
	PYTHONPATH=src python -c "\
import asyncio; \
from sqlalchemy.ext.asyncio import create_async_engine; \
from infrastructure.db.models import Base; \
from api.config import get_settings; \
settings = get_settings(); \
engine = create_async_engine(settings.database_url); \
asyncio.run(engine.run_sync(Base.metadata.create_all)); \
print('Tables created.')"
