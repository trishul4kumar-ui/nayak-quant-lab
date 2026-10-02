PYTHON ?= .venv/bin/python
PYTEST = $(PYTHON) -m pytest
RUFF = $(PYTHON) -m ruff
MYPY = $(PYTHON) -m mypy

.PHONY: install lint typecheck test test-core test-ui slice desktop all

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(RUFF) check src tests
	$(RUFF) format --check src tests

format:
	$(RUFF) format src tests

typecheck:
	$(MYPY) src/quantlab

test-core:
	$(PYTEST) tests/unit tests/risk tests/backtest tests/end_to_end tests/research tests/execution tests/execution_research tests/orchestration tests/discovery tests/knowledge tests/capital tests/paper_oms tests/monitoring tests/tca tests/econometrics tests/certification tests/shadow tests/safety tests/ops tests/release tests/broker_gateway tests/realtime_data tests/realtime_decision tests/digital_twin tests/production_shadow tests/execution_authorization tests/restricted_execution tests/live_ops tests/app tests/data tests/features tests/labels tests/alpha tests/portfolio tests/factors tests/regimes tests/adaptive tests/learning tests/ensemble

test-ui:
	QT_QPA_PLATFORM=offscreen QUANT_LAB_SKIP_SPLASH=1 $(PYTEST) tests/ui

test: test-core test-ui

slice:
	$(PYTEST) -m vertical_slice

desktop:
	@$(PYTHON) -c "import quantlab.ui" 2>/dev/null || { \
		echo "Package not installed. Run: make install"; \
		exit 1; \
	}
	@echo "Starting NAYAK QUANT LAB (native window — terminal will stay open)…"
	$(PYTHON) -m quantlab.ui

all: lint typecheck test
