.PHONY: setup check install dev test lint scan serve daemon doctor ui pages check-paths smoke fresh-clone

setup:
	./scripts/setup.sh

check:
	./scripts/setup.sh --check

install:
	python -m pip install -e '.[dev]'

dev:
	uvicorn hermes_maintainer.api.app:create_app --factory --reload --host 127.0.0.1 --port 8766

test:
	pytest -q

lint:
	ruff check .

scan:
	hermes-maintainer scan --mode fast --limit 100

serve:
	hermes-maintainer serve

daemon:
	hermes-maintainer daemon

doctor:
	hermes-maintainer doctor

ui:
	./scripts/build-ui.sh

pages:
	python3 scripts/build-pages.py

check-paths:
	./scripts/check-no-local-paths.sh

smoke:
	.venv/bin/python scripts/smoke-serve.py

fresh-clone:
	./scripts/fresh-clone-check.sh
