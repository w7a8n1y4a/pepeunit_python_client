.PHONY: help install-local run-build upload-pypi upload-test-pypi clean

help:
	@echo "Pepeunit Python Client - Commands:"
	@echo ""
	@echo "install-local:    Build and install the wheel"
	@echo "run-build:        Run build package"
	@echo "upload-pypi:      Upload dist to PyPi"
	@echo "upload-test-pypi: Upload dist to Test PyPi"
	@echo "clean:            Clean venv and dist"

install-local: run-build
	python -m venv .venv
	.venv/bin/python -m pip install --force-reinstall "$(wildcard dist/*.whl)"
	@echo "Activate the environment with source .venv/bin/activate"

run-build:
	@echo "Run build package"
	rm -rf dist
	python -m build

upload-pypi:
	@echo "Upload dist to PyPi"
	twine upload dist/*

upload-test-pypi:
	@echo "Upload dist to Test PyPi"
	twine upload --repository testpypi dist/*

clean:
	@echo "Clean venv and dist..."
	rm -rf .venv dist
