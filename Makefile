.PHONY: setup verify test

setup:
	bash scripts/setup.sh

verify:
	python3 aion_cycle.py

test:
	python3 -m pytest tests -q
