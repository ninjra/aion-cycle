.PHONY: setup verify-ptau demo verify verify-explain prove reproduce break redteam inspect explain fixtures boundary-check test viewer

setup:
	bash scripts/setup.sh

verify-ptau:
	AION_VERIFY_PTAU=1 bash scripts/setup.sh

demo:
	@echo "AION demo: fixed canonical reference cycle"
	@echo "command: python3 aion_cycle.py --verify-statement aion.statement.json"
	@python3 aion_cycle.py --verify-statement aion.statement.json
	@echo "inspect: aion.statement.json"
	@echo "inspect: proofs/v1/proof-artifacts.receipt.json"

verify:
	python3 aion_cycle.py --verify-statement aion.statement.json

verify-explain:
	python3 aion_cycle.py --verify-statement aion.statement.json --explain

reproduce:
	python3 aion_cycle.py

prove: reproduce

break:
	bash scripts/break_demo.sh

redteam:
	python3 -m pytest tests/test_redteam.py -q

inspect:
	@echo "statement:"; cat aion.statement.json
	@echo "proof-artifacts receipt:"; cat proofs/v1/proof-artifacts.receipt.json

explain:
	@echo "AION v1 proves route truth for one fixed canonical reference cycle."
	@echo "Commands: make demo | verify | verify-explain | break | redteam | reproduce | inspect"
	@echo "Read order: README.md -> PUBLIC_BOUNDARY.md -> VERIFY.md -> TRUSTED_SETUP.md -> PUBLIC_CLAIMS.md -> DESIGN_NOTES.md"
	@echo "Artifacts: aion.statement.json, proofs/v1/proof.json, proofs/v1/public.json, proofs/v1/proof-artifacts.receipt.json, proofs/v1/receipts/"

fixtures:
	@find fixtures -maxdepth 2 -name README.md -print | sort

boundary-check:
	python3 -m pytest tests/test_public_boundary.py -q

test:
	python3 -m pytest tests -q

viewer:
	@echo "Open viewer/index.html locally in a browser. It is read-only and performs no verification."
