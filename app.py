import os
import uuid
import subprocess
import threading
import json
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder='static')
CORS(app)

OUTPUT_DIR = '/output'
downloads = {}  # In-memory store: {id: {...}}
lock = threading.Lock()


def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()


def run_download(dl_id, url, quality, fmt):
    with lock:
        downloads[dl_id]['status'] = 'downloading'

    quality_map = {
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '1440p': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '4k':    'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
    }

    format_str = quality_map.get(quality, quality_map['1080p'])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_template = os.path.join(OUTPUT_DIR, f'%(title)s_{timestamp}.%(ext)s')

    cmd = [
        'yt-dlp',
        '--no-playlist',
        '--live-from-start',
        '-f', format_str,
        '--merge-output-format', fmt,
        '--newline',
        '-o', out_template,
        url
    ]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        with lock:
            downloads[dl_id]['pid'] = proc.pid

        log_lines = []
        for line in proc.stdout:
            line = line.strip()
            if line:
                log_lines.append(line)
                if len(log_lines) > 100:
                    log_lines = log_lines[-100:]
                with lock:
                    downloads[dl_id]['log'] = log_lines
                    # Try to extract progress info
                    if '[download]' in line:
                        downloads[dl_id]['progress'] = line

        proc.wait()
        with lock:
            if proc.returncode == 0:
                downloads[dl_id]['status'] = 'completed'
            else:
                downloads[dl_id]['status'] = 'error'
                downloads[dl_id]['error'] = f'Process exited with code {proc.returncode}'
    except Exception as e:
        with lock:
            downloads[dl_id]['status'] = 'error'
            downloads[dl_id]['error'] = str(e)


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/downloads', methods=['GET'])
def list_downloads():
    with lock:
        return jsonify(list(downloads.values()))


@app.route('/api/downloads', methods=['POST'])
def start_download():
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', '1080p')
    fmt = data.get('format', 'mp4')

    if not url:
        return jsonify({'error': 'URL is required'}), 400
    if quality not in ('1080p', '1440p', '4k'):
        return jsonify({'error': 'Invalid quality'}), 400
    if fmt not in ('mp4', 'mkv'):
        return jsonify({'error': 'Invalid format'}), 400

    dl_id = str(uuid.uuid4())
    entry = {
        'id': dl_id,
        'url': url,
        'quality': quality,
        'format': fmt,
        'status': 'queued',
        'started_at': datetime.now().isoformat(),
        'progress': '',
        'log': [],
        'error': '',
        'pid': None,
    }

    with lock:
        downloads[dl_id] = entry

    t = threading.Thread(target=run_download, args=(dl_id, url, quality, fmt), daemon=True)
    t.start()

    return jsonify(entry), 201


@app.route('/api/downloads/<dl_id>', methods=['GET'])
def get_download(dl_id):
    with lock:
        dl = downloads.get(dl_id)
    if not dl:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dl)


@app.route('/api/downloads/<dl_id>', methods=['DELETE'])
def cancel_download(dl_id):
    with lock:
        dl = downloads.get(dl_id)
    if not dl:
        return jsonify({'error': 'Not found'}), 404

    pid = dl.get('pid')
    if pid:
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass

    with lock:
        downloads[dl_id]['status'] = 'cancelled'

    return jsonify({'ok': True})


@app.route('/api/downloads/<dl_id>/log', methods=['GET'])
def get_log(dl_id):
    with lock:
        dl = downloads.get(dl_id)
    if not dl:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'log': dl.get('log', [])})


if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
