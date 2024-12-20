# Makefile for Flask Application with Gunicorn

# Declare phony targets to prevent conflicts with files of the same name
.PHONY: install run test clean dev update

# Variables
VENV_DIR := venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
GUNICORN := $(VENV_DIR)/bin/gunicorn
APP_MODULE := app:app
BIND := 0.0.0.0:5000
REQUIREMENTS := requirements.txt

# Target: Create a virtual environment and install dependencies
install:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV_DIR)
	@echo "Activating virtual environment and installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r $(REQUIREMENTS)
	@echo "Installation complete."

# Target: Run the Flask application using Gunicorn
run:
	@echo "Starting the Flask application with Gunicorn..."
	$(GUNICORN) --bind $(BIND) $(APP_MODULE)

# Target: Run the Flask application in development mode using Flask's built-in server
dev:
	@echo "Starting the Flask development server..."
	$(PYTHON) -m flask run --host=0.0.0.0 --port=5000

# Target: Run tests (assuming you have tests set up)
test:
	@echo "Running tests..."
	$(PYTHON) -m unittest discover -s tests
	@echo "Tests completed."

# Target: Clean up virtual environment and Python cache files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup complete."

# Optional: Update dependencies
update:
	@echo "Updating dependencies..."
	$(PIP) install --upgrade -r $(REQUIREMENTS)
	@echo "Dependencies updated."
