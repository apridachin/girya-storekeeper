#!/bin/bash

# Deploy script for Girya Storekeeper

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check and install Docker if needed
ensure_docker() {
    if command_exists docker; then
        echo "✓ Docker is already installed"
    else
        echo "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
        echo "! Please log out and log back in for Docker permissions to take effect"
        exit 1
    fi

    if command_exists docker-compose; then
        echo "✓ Docker Compose is already installed"
    else
        echo "Installing Docker Compose..."
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
}

# Configure firewall if UFW is installed
setup_firewall() {
    if command_exists ufw; then
        echo "Configuring firewall..."
        sudo ufw status | grep -q "Status: active" || {
            sudo ufw allow 22/tcp
            sudo ufw allow 80/tcp
            sudo ufw allow 443/tcp
            sudo ufw --force enable
        }
        echo "✓ Firewall configured"
    else
        echo "! UFW not installed, skipping firewall configuration"
    fi
}

# Main deployment function
deploy() {
    echo "Starting deployment..."
    
    # Check if git repo exists
    if [ ! -d .git ]; then
        echo "! Not a git repository. Please run this script from the project root."
        exit 1
    fi

    # Pull latest changes if remote exists
    if git remote -v | grep -q origin; then
        echo "Pulling latest changes..."
        git pull origin master || {
            echo "! Failed to pull latest changes"
            echo "Continuing with existing code..."
        }
    fi

    # Copy environment file if not exists
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "! Please edit .env file with your production values"
        echo "Then run this script again"
        exit 1
    fi

    echo "Starting Docker services..."
    # Build and start containers
    docker-compose down
    docker-compose pull
    docker-compose up -d --build

    # Check if services are running
    echo "Checking services..."
    sleep 5
    if docker-compose ps | grep -q "Up"; then
        echo "✓ Services are running"
        echo "Application is now available at http://$(curl -s ifconfig.me)"
    else
        echo "! Some services failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
}

# Main script
echo "Girya Storekeeper Deployment"
echo "==========================="

# Ensure Docker is installed and running
ensure_docker

# Setup firewall
setup_firewall

# Run deployment
deploy
