.PHONY: up down seed test validate lint type-check clean

up:
	docker compose up -d

down:
	docker compose down

seed:
	python backend/seed.py

test:
	pytest backend/tests/ -v --tb=short

validate:
	python backend/parser/excel_parser.py --input "time_table/ACSE TIMETABLE (V5)  - W.e.f 15-7-2026.xlsx" --validate-only

lint:
	ruff check backend/
	cd frontend && npm run lint

type-check:
	mypy backend/ --strict
	cd frontend && npm run type-check

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
