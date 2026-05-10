.PHONY: all build start test clean

all: build start

build:
	@echo "Building OmniTwin Architecture (CUDA, Rust, and Python)..."
	docker-compose build

start:
	@echo "Starting OmniTwin Cluster..."
	docker-compose up -d

stop:
	@echo "Stopping OmniTwin Cluster..."
	docker-compose down

test:
	@echo "Running local sovereign integration tests..."
	PYTHONPATH=. pytest tests/ -v

clean:
	@echo "Cleaning cache and build artifacts..."
	rm -rf src/__pycache__ src/**/*.pyc src/**/__pycache__
	rm -rf omnitwin_codebase.zip
