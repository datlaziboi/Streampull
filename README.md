# StreamPull — YouTube Live Stream Downloader

A self-hosted web app for downloading YouTube live streams, packaged as a Docker container.

## Features
- Web UI accessible in any browser
- Download live streams in **1080p**, **1440p**, or **4K**
- Output format: **MP4** or **MKV**
- View active/queued/completed downloads in real-time
- Cancel in-progress downloads
- Expand download log output per job
- All videos saved to the local `./output` folder

## Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Deploy

```bash
git clone <this-repo>
cd yt-stream-downloader

# Build and start
docker compose up -d --build

# Open the web UI
open http://localhost:8080
```

### Stop

```bash
docker compose down
```

## Usage

1. Open **http://localhost:8080** in your browser
2. Paste a YouTube live stream URL
3. Choose quality (1080p / 1440p / 4K) and format (MP4 / MKV)
4. Click **▶ START**
5. Watch progress in the downloads list (auto-refreshes every 3 seconds)
6. Click any row to expand the raw yt-dlp log
7. Finished files appear in `./output/`

## Configuration

| Variable | Default | Description |
|---|---|---|
| Port (host) | `8080` | Change in `docker-compose.yml` under `ports` |
| Output dir | `./output` | Change the volume mount in `docker-compose.yml` |

## Notes

- Live streams are downloaded **from the beginning** (`--live-from-start`). For streams already in progress, yt-dlp will grab what's available.
- 4K requires the source stream to actually be broadcasting in 4K; otherwise yt-dlp will fall back to the best available quality.
- yt-dlp is installed inside the container; no need to install it on the host.
- ffmpeg is included for proper audio+video merging into MP4/MKV containers.
