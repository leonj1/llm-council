# Makefile for LLM Council Docker operations

# Variables
IMAGE_NAME = llm-council
CONTAINER_NAME = llm-council
PORT = 8004
DATA_DIR = $(PWD)/data

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME):latest .

# Start the container
start:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p $(PORT):$(PORT) \
		-v $(DATA_DIR):/app/data \
		-v $(DATA_DIR)/tailscale:/var/lib/tailscale \
		--cap-add=NET_ADMIN \
		--device=/dev/net/tun:/dev/net/tun \
		--env-file .env \
		$(IMAGE_NAME):latest

# Stop the container
stop:
	docker stop -t 0 $(CONTAINER_NAME) || true
	docker rm -f $(CONTAINER_NAME) || true

# Restart the container
restart: stop start

# Run tests in Docker containers
test:
	@echo "Starting test environment..."
	docker compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
	docker compose -f docker-compose.test.yml build test-runner
	docker compose -f docker-compose.test.yml up --abort-on-container-exit --exit-code-from test-runner
	@echo "Cleaning up test environment..."
	docker compose -f docker-compose.test.yml down -v --remove-orphans

.PHONY: build start stop restart test
