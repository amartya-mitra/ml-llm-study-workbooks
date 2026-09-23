PYTHON ?= python3

.PHONY: validate validate-registry validate-questions figures workbooks \
        render-sample review-ch01-02 review-ch01-03 review-ch01-04 review-ch01-05 \
        review-ch01-06 test check-links clean

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
# SUPERSEDED as a live target now that index.qmd includes Chapter 3 --
# running this now renders the same 3-chapter document and would
# mislabel it; kept only so outputs/04-llm-architecture-ch01-02-review.pdf's
# frozen historical artifact and build script remain traceable. Use
# review-ch01-03 instead.
review-ch01-02:
	$(PYTHON) scripts/build_ch01_02_review.py

# Build the Chapters 1-3 review PDF (see scripts/build_ch01_03_review.py).
# SUPERSEDED as a live target now that index.qmd includes Chapter 4 --
# use review-ch01-04 instead; kept for traceability of the frozen
# outputs/04-llm-architecture-ch01-03-review.pdf artifact.
review-ch01-03:
	$(PYTHON) scripts/build_ch01_03_review.py

# Build the Chapters 1-4 review PDF (see scripts/build_ch01_04_review.py).
# SUPERSEDED as a live target now that index.qmd includes Chapter 5 --
# use review-ch01-05 instead; kept for traceability of the frozen
# outputs/04-llm-architecture-ch01-04-review.pdf artifact.
review-ch01-04:
	$(PYTHON) scripts/build_ch01_04_review.py

# Build the Chapters 1-5 review PDF (see scripts/build_ch01_05_review.py).
# SUPERSEDED as a live target now that index.qmd includes Chapter 6 --
# use review-ch01-06 instead; kept for traceability of the frozen
# outputs/04-llm-architecture-ch01-05-review.pdf artifact.
review-ch01-05:
	$(PYTHON) scripts/build_ch01_05_review.py

# Build the Chapters 1-6 review PDF (see scripts/build_ch01_06_review.py).
review-ch01-06:
	$(PYTHON) scripts/build_ch01_06_review.py

# Network-dependent: checks that every sources/registry.yaml URL responds.
check-links:
	$(PYTHON) scripts/check_links.py

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
