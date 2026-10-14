from flask import Flask, render_template
from routes import api
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.json.ensure_ascii = False

app.register_blueprint(api)


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )