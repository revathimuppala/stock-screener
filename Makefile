.PHONY: backend-install backend-test backend-dev frontend-install frontend-test frontend-lint e2e dev

backend-install:
	cd backend && poetry install --no-root

backend-test:
	cd backend && poetry run pytest

backend-dev:
	cd backend && PYTHONPATH=src poetry run uvicorn screener.api.main:app --reload --port 8000

frontend-install:
	cd frontend && npm install

frontend-test:
	cd frontend && npm test

frontend-lint:
	cd frontend && npx eslint .

frontend-dev:
	cd frontend && npm run dev

e2e:
	cd frontend && npx playwright test

dev:
	$(MAKE) -j2 backend-dev frontend-dev
