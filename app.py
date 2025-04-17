from flask import Flask, render_template, request
import joblib
import re
import string

app = Flask(__name__)

# Load model
model = joblib.load("model/model.sav")

# Load vectorizer
vectorizer = joblib.load("model/vectorizer.sav")

# Text cleaning function
def clean_text(text):
    text = text.lower()
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = ""
    if request.method == "POST":
        user_input = request.form["user_input"]
        cleaned_input = clean_text(user_input)
        vectorized_input = vectorizer.transform([cleaned_input])
        prediction = model.predict(vectorized_input)[0]
    return render_template("index.html", prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)
