CONFIG_TEMPLATE = """
# Example Atlas Ops configuration
project: atlas-core
environment: dev

requirements:
  - name: python
    description: Verify that Python is available
    check: python --version
  - name: git
    description: Ensure git CLI is present
    check: git --version

# Tasks are run in order, each containing one or more steps.
tasks:
  bootstrap:
    description: Install dependencies and prepare the workspace
    steps:
      - run: python -m venv .venv
      - run: .venv/bin/pip install -U pip
      - run: .venv/bin/pip install -r requirements.txt
  lint:
    description: Run static analysis across the codebase
    steps:
      - run: .venv/bin/python -m compileall src
      - run: .venv/bin/flake8 src
  deploy:
    description: Build and release the service
    steps:
      - run: make build
      - run: make deploy
"""
