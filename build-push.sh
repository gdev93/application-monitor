#!/bin/bash

# Build and Push Script for application-monitor Docker Image
# Usage: ./build-and-push.sh [tag]

set -e  # Exit on any error

# Configuration
IMAGE_NAME="giacomodev93/application-monitor"
VERSION_FILE="VERSION"
DOCKERFILE="Dockerfile"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Read version from VERSION file or use provided tag
if [ -f "$VERSION_FILE" ]; then
    DEFAULT_TAG=$(cat "$VERSION_FILE" | tr -d '[:space:]')
    log_info "Version read from $VERSION_FILE: $DEFAULT_TAG"
else
    DEFAULT_TAG="1.0.0"
    log_warning "VERSION file not found, using default tag: $DEFAULT_TAG"
fi

# Get tag from argument or use version from file
TAG=${1:-$DEFAULT_TAG}
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

log_info "Starting build and push process for ${FULL_IMAGE_NAME}"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    log_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "$DOCKERFILE" ]; then
    log_error "Dockerfile not found in current directory"
    exit 1
fi

# Build the image
log_info "Building and pushing docker image: ${FULL_IMAGE_NAME}"
if docker buildx build --push --platform linux/amd64,linux/arm64 -t "${FULL_IMAGE_NAME}" -f "$DOCKERFILE" .; then
    log_success "Docker image built and pushed successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

log_success "All done! 🚀"