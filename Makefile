.PHONY: help install dev dev-backend dev-frontend test eval lint build clean

help:
	@echo "ClauseLens - Residential Tenancy Compliance & Logic Verification Engine"
	@echo ""
	@echo "Commands:"
	@echo "  make install       Install backend (pip) and frontend (npm) dependencies"
	@echo "  make test          Run full pytest test suite (16 tests across logic, pipeline, api)"
	@echo "  make eval          Execute benchmark evaluation harness and update docs/EVAL_RESULTS.md"
	@echo "  make lint          Run code style checks (ruff for python)"
	@echo "  make build         Compile production React/TypeScript assets"
	@echo "  make dev-backend   Start FastAPI server on http://localhost:8000"
	@echo "  make dev-frontend  Start Vite development server on http://localhost:5173"
	@echo "  make dev           Start both backend and frontend development servers"

install:
	python -m pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	python -m pytest backend/tests -v

eval:
	python -m backend.eval.run_eval

lint:
	python -m ruff check backend/

build:
	cd frontend && npm run build

dev-backend:
	python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting ClauseLens backend and frontend..."
	python -m uvicorn backend.app.main:app --port 8000 & cd frontend && npm run dev

clean:
	rm -rf dist frontend/dist .pytest_cache .ruff_cache

