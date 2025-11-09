# NBA Watcher

A lightweight Flask web application for tracking and streaming live NBA games. The application displays a list of today's or tomorrow's games, provides live scores and key player stats, and includes an embeddable stream viewer with box score updates.

---

## ✨ Features

- **Game Listings:** Displays a list of scheduled NBA games.
- **Live Scoreboard:** Fetches real-time scores, game status (e.g., quarter, time remaining), and leaders for active games.
- **Team Branding:** Uses official team colors and logos.
- **Embedded Streams:** Provides a dedicated page for streaming the game.
- **Live Box Score:** Displays player statistics, highlighting starters and players currently on the court, with data polled and updated every 10 seconds.

---

## 🛠 Prerequisites: Install Docker

This project is configured to run easily using **Docker**. You must have Docker Engine (typically via **Docker Desktop**) installed on your machine. Follow the instructions for your specific operating system:

## 1. Install Docker on macOS

The simplest method for macOS users who have the [Homebrew](https://brew.sh/) package manager installed is to use Homebrew Cask to install Docker Desktop:

```bash
# Install Docker Desktop via Homebrew Cask
brew install --cask docker
# Launch the application
open /Applications/Docker.app
```

## 2. Install Docker on Windows

Download and Install Docker Desktop: Download the installer from the official Docker Desktop [website](https://www.docker.com/products/docker-desktop/).

Enable WSL 2: During installation, ensure the option to Enable WSL 2 is selected for optimal performance. You may need to run `wsl --install` in PowerShell as an administrator if WSL is not already enabled.

Start Docker: Launch Docker Desktop after installation and wait for it to fully start.

---

## 3. Install Docker on Linux (e.g., Ubuntu/Debian)

While Docker Engine (CLI only) is available via package managers, Docker Desktop for Linux is highly recommended for a full user experience.

### A. Docker Desktop (Recommended):

Download the correct .deb or .rpm package from the official Docker Desktop for Linux documentation.

Install the package using your system's package manager (e.g., `sudo apt install ./docker-desktop-VERSION-ARCH.deb`).

Start the application.

### B. Docker Engine (CLI Only):

```bash
sudo apt update
```

#### Install Docker Engine (docker.io on Ubuntu/Debian)

```bash
sudo apt install -y docker.io
```

#### Start and enable the Docker service

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

#### Optional: Add user to 'docker' group (log out/in to apply)

```bash
sudo usermod -aG docker $USER
```

---

## 🚀 Getting Started (Docker)

These instructions will get a copy of the project running in a container on your local machine.

### 1. Build the Docker Image

Navigate to the project's root directory (where the `Dockerfile` and `app.py` are located) and run the build command:

```bash
docker build -t nba-watcher .
```

### 2. Run the Container

We use port **5001** on the host machine to map to the container's internal port **5000** to avoid common port conflicts:

```bash
docker run -d -p 5001:5000 --env-file .env --name nba-watcher-app nba-watcher
```

### 3. Access the Application

Open your web browser and navigate to:
http://localhost:5001
