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

.PHONY: build start stop restart
