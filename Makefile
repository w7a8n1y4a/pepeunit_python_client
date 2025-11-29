.PHONY: help install-local run-build upload-pypi upload-test-pypi clean

help:
	@echo "Pepeunit Python Client - Commands:"
	@echo ""
	@echo "install-local:    Clean create dist and .venv and install package from dist" 
	@echo "run-build:        Run build package"
	@echo "upload-pypi:      Upload dist to PyPi"
	@echo "upload-test-pypi: Upload dist to Test PyPi"
	@echo "clean:            Clean venv and dist"

install-local:
	@echo "Clean create dist and .venv and install package from dist..."
	rm -rf .venv dist
	python -m build
	python -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install dist/*.whl
	.venv/bin/pip install httpx paho-mqtt cryptography
	@echo "Done! Activate with: source .venv/bin/activate.fish"

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
