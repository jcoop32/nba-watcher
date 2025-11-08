# 🏀 NBA Watcher

A lightweight Flask web application for tracking and streaming live NBA games. The application displays a list of today's or tomorrow's games, provides live scores and key player stats, and includes an embeddable stream viewer with box score updates.

---

## ✨ Features

- **Game Listings:** Displays a list of scheduled NBA games.
- **Live Scoreboard:** Fetches real-time scores, game status (e.g., quarter, time remaining), and leaders for active games.
- **Team Branding:** Uses official team colors and logos.
- **Embedded Streams:** Provides a dedicated page for streaming the game.
- **Live Box Score:** Displays player statistics, highlighting starters and players currently on the court, with data polled and updated every 10 seconds.

---

## 🛠 Prerequisites

This project is configured to run easily using **Docker**. You must have [Docker Engine](https://www.docker.com/products/docker-desktop/) installed on your machine.

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
docker run -d -p 5001:5000 --name nba-watcher-app nba-watcher
```

### 3. Access the Application

Open your web browser and navigate to:
http://localhost:5001
