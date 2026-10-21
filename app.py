from flask import Flask, render_template
from routes import api

app = Flask(__name__)
app.register_blueprint(api)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/courses-page")
def courses_page():
    return render_template("courses.html")

@app.route("/students-page")
def students_page():
    return render_template("students.html")

@app.route("/enrollments-page")
def enrollments_page():
    return render_template("enrollments.html")

@app.route("/recommend-page")
def recommend_page():
    return render_template("recommend.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)