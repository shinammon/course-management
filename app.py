from flask import Flask
from routes import api

app = Flask(__name__)

app.json.ensure_ascii = False

app.register_blueprint(api)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )