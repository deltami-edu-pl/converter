#!/usr/bin/env python3

import os
import signal
import socket
import subprocess
import sys
import time
from config import FILE
from flask import Flask, send_from_directory, abort, render_template


PORT = 5000


def is_port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def kill_stale_flask(port: int) -> None:
    """Jesli na porcie wisi nasz stary Flask (z poprzedniej sesji ktora padla),
    ubij go. Procesow systemowych (np. ControlCenter/AirPlay) nie ruszamy."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return
    pids = [p for p in result.stdout.strip().split() if p]
    for pid_str in pids:
        try:
            pid = int(pid_str)
            cmd = subprocess.run(
                ["ps", "-p", str(pid), "-o", "command="],
                capture_output=True, text=True, check=False,
            ).stdout
        except (ValueError, FileNotFoundError):
            continue
        if "a6_serve" in cmd or ("python" in cmd and "main.py" in cmd):
            print(f"# Stary serwer Flask wisi na :{port} (PID {pid}) - ubijam")
            try:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.5)
                if not is_port_free(port):
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.3)
            except ProcessLookupError:
                pass


def serve():
    app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

    # @app.route("/")
    # def home():
    #     filtered_files = [f for f in os.listdir(".") if f.endswith("-article.html")]
    #     print("home")
    #     print(filtered_files)
    #     return "<br />".join(
    #         sorted(map(lambda f: f"<a href='{f}'>{f}</a>", filtered_files))
    #     )

    @app.route("/media/<path:filename>")
    def serve_media_file(filename):
        # Konstrukcja ścieżki bez prefiksu "/media"
        local_path = os.path.join(".", filename)

        # Sprawdzenie, czy plik istnieje
        if os.path.isfile(local_path):
            return send_from_directory(".", filename)
        else:
            # Zwrot błędu 404, jeśli plik nie istnieje
            abort(404)

    @app.route("/")
    def serve_html_file():
        # Sprawdzamy, czy plik istnieje i czy kończy się na .html
        # if filename.endswith(".html") and os.path.isfile(os.path.join(".", filename)):
        # if os.path.isfile(os.path.join(".", filename)):
        #     if not filename.endswith(".html"):
        #         return send_from_directory(".", filename)
        #     else:
        #         with open(filename, "r") as file:
        #             content = file.read()
        content = FILE().article.html.read_text(encoding="utf-8")
        return render_template(
            "static/template.html", title='artykul', content=content
        )

        # else:
        #     abort(404)

    # Flask debug=True spawnuje child przez Werkzeug reloader. Cleanup robimy
    # tylko w parencie (WERKZEUG_RUN_MAIN nie jest 'true'), inaczej child by
    # ubil rodzica matchujac sie z `main.py` w cmdline. Port przekazujemy do
    # childa przez env var, zeby nie powtarzac wyboru portu.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        port = int(os.environ.get("DELTA_PORT", PORT))
    else:
        port = PORT
        if not is_port_free(port):
            kill_stale_flask(port)
        if not is_port_free(port):
            print(f"# Port {port} zajety (zwykle macOS AirPlay Receiver)")
            print(f"#   wylacz: System Settings -> General -> AirDrop & Handoff -> AirPlay Receiver")
            port = 5050
            if not is_port_free(port):
                kill_stale_flask(port)
            if not is_port_free(port):
                print(f"# ERROR: {port} tez zajety - sprawdz lsof -i :{port}")
                sys.exit(1)
            print(f"# Uzywam {port} zamiast {PORT}")
        os.environ["DELTA_PORT"] = str(port)
        print(f"# Serwer na http://localhost:{port}/")
    app.run(debug=True, port=port)


if __name__ == "__main__":
    serve()
