# Kassanjee v9 manuscript — reproducibility convenience targets
# Operator: Dr. A.C. Demidont, DO
#
# Usage: make <target>   (run `make help` for the menu)

.PHONY: help reproduce reproduce-fast verify clean clean-runs

help:
	@echo "Kassanjee v9 reproducibility targets:"
	@echo ""
	@echo "  make reproduce       Full pipeline: ingest → figures → COVID → verify  (~3 min)"
	@echo "  make reproduce-fast  Numbers only, skip figures and COVID figure       (~30 s)"
	@echo "  make verify          Re-run verification on the latest run directory"
	@echo "  make clean           Remove __pycache__ and *.pyc"
	@echo "  make clean-runs      Remove ALL run directories (prompts for confirmation)"
	@echo ""
	@echo "See REPRODUCE.md for environment setup and stage-by-stage reproduction."

reproduce:
	python reproduce_v9.py

reproduce-fast:
	python reproduce_v9.py --skip-figures

verify:
	@latest=$$(ls -td runs/*/ 2>/dev/null | head -n1); \
	if [ -z "$$latest" ]; then \
		echo "No run directories found. Run 'make reproduce' first."; \
		exit 1; \
	fi; \
	echo "Verifying latest run: $$latest"; \
	python verify_v9.py \
	    --statistics-csv $${latest}Statistics_Summary.csv \
	    --expected-csv expected_v9_statistics.csv

clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "Removed __pycache__ and *.pyc files."

clean-runs:
	@read -p "Delete ALL run directories under runs/? [y/N] " ans; \
	if [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; then \
		rm -rf runs/; \
		echo "Removed runs/"; \
	else \
		echo "Aborted."; \
	fi
