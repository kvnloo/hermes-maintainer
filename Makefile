.PHONY: install dev test lint scan serve daemon doctor ui

install:
	python -m pip install -e '.[dev]'

dev:
	uvicorn hermes_maintainer.api.app:create_app --factory --reload --host 127.0.0.1 --port 8766

test:
	pytest -q

lint:
	ruff check .

scan:
	hermes-maintainer scan --mode fast

serve:
	hermes-maintainer serve

daemon:
	hermes-maintainer daemon

doctor:
	hermes-maintainer doctor

ui:
	./scripts/build-ui.sh
