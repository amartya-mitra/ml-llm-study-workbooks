PYTHON ?= python3

.PHONY: validate validate-registry validate-questions figures workbooks \
        render-sample review-ch01-02 test check-links clean

# Run every offline (non-network) validation check.
validate: validate-registry validate-questions

validate-registry:
	$(PYTHON) scripts/validate_registry.py

validate-questions:
	$(PYTHON) scripts/validate_questions.py

# Regenerate all figures/rendered/*.svg from figures/source/*.py.
figures:
	$(PYTHON) scripts/build_figures.py

# Render every workbooks/**/*.qmd via Quarto (requires quarto on PATH).
workbooks:
	$(PYTHON) scripts/build_workbooks.py

# Render the Stage 7 bootstrap sample and run the pdfinfo/pdftotext/pdftoppm
# inspection pipeline (requires quarto + poppler-utils on PATH).
render-sample:
	$(PYTHON) scripts/render_and_check.py workbooks/04-llm-architecture/bootstrap-sample.qmd

# Build the Chapters 1-2 review PDF: regenerate figures + build note,
# render via Quarto/Typst, copy to outputs/, then run the
# pdfinfo/pdftotext/pdffonts/pdftoppm inspection pipeline (requires
# quarto + poppler-utils on PATH -- activate the ml-workbooks conda env).
review-ch01-02:
	$(PYTHON) scripts/build_ch01_02_review.py

# Network-dependent: checks that every sources/registry.yaml URL responds.
check-links:
	$(PYTHON) scripts/check_links.py

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
