.PHONY: install lint typecheck test slice desktop all

install:
	python3 -m pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff format src tests

typecheck:
	mypy src/quantlab

test:
	pytest tests/unit tests/risk tests/backtest tests/end_to_end tests/research tests/execution tests/execution_research tests/orchestration tests/discovery tests/knowledge tests/capital tests/paper_oms tests/monitoring tests/tca tests/econometrics tests/certification tests/shadow tests/safety tests/ops tests/release tests/broker_gateway tests/realtime_data tests/realtime_decision tests/digital_twin tests/app tests/data tests/features tests/labels tests/alpha tests/portfolio tests/factors tests/regimes tests/adaptive tests/learning tests/ensemble
	QT_QPA_PLATFORM=offscreen QUANT_LAB_SKIP_SPLASH=1 pytest tests/ui

slice:
	pytest -m vertical_slice

desktop:
	@python -c "import quantlab.ui" 2>/dev/null || { \
		echo "Package not installed. Run: make install"; \
		exit 1; \
	}
	@echo "Starting NAYAK QUANT LAB (native window — terminal will stay open)…"
	python -m quantlab.ui

all: lint typecheck test
