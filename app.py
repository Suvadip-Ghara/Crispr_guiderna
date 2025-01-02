from flask import Flask, render_template, request
from scraping.scraper import scrape_idtdna

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    fasta_sequence = request.form["sequence"]
    results = scrape_idtdna(fasta_sequence)
    if results:
        return render_template("results.html", results=results)
    else:
        return "Error fetching results", 500

if __name__ == "__main__":
    app.run(debug=True)
