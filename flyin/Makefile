VENV_DIR := venv
PYTHON   := python3
BIN      := $(VENV_DIR)/bin
MAIN     := fly_in.py

.PHONY: all install run debug clean fclean lint lint-strict

all: install

$(BIN)/activate:
	$(PYTHON) -m venv $(VENV_DIR)

install: $(BIN)/activate
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install pygame flake8 mypy
	$(BIN)/pip install flake8


run: $(BIN)/activate
	$(BIN)/python $(MAIN) $(MAP)

debug: $(BIN)/activate
	$(BIN)/python -m pdb $(MAIN) $(MAP)

clean:
	find . -type d -name "__pycache__" -not -path "./$(VENV_DIR)/*" -exec rm -rf {} +
	rm -rf .mypy_cache

fclean: clean
	rm -rf $(VENV_DIR)

lint:
	$(BIN)/flake8 . --exclude $(VENV_DIR)
	$(BIN)/mypy . --exclude $(VENV_DIR) --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(BIN)/flake8 . --exclude $(VENV_DIR)
	$(BIN)/mypy . --exclude $(VENV_DIR) --strict