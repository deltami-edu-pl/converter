#!/usr/bin/env python3

import os
from flask import Flask, send_from_directory, abort, render_template


def serve():
    app = Flask(__name__, template_folder=os.path.dirname(os.path.abspath(__file__)))

    @app.route("/")
    def home():
        filtered_files = [f for f in os.listdir(".") if f.endswith("-article.html")]
        print("home")
        print(filtered_files)
        return "<br />".join(
            sorted(map(lambda f: f"<a href='{f}'>{f}</a>", filtered_files))
        )

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

    @app.route("/<path:filename>")
    def serve_html_file(filename):
        # Sprawdzamy, czy plik istnieje i czy kończy się na .html
        # if filename.endswith(".html") and os.path.isfile(os.path.join(".", filename)):
        if os.path.isfile(os.path.join(".", filename)):
            if not filename.endswith(".html"):
                return send_from_directory(".", filename)
            else:
                with open(filename, "r") as file:
                    content = file.read()
                return render_template(
                    "static/template.html", title=filename, content=content
                )

        else:
            abort(404)

    app.run(debug=True)


if __name__ == "__main__":
    serve()
