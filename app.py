import os
from flask import Flask, render_template, request
from crawler import search
from helpers import scrape_wikipedia_articles
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

app = Flask(__name__)
# Define the categories
categories = ['Sport', 'Technology', 'Climate']

# Load the documents into a pandas DataFrame
# Each row should contain a document
csv_path = os.path.join(os.path.dirname(__file__), 'articles.csv')
if not os.path.isfile(csv_path):
    scrape_wikipedia_articles()
df = pd.read_csv(csv_path, names=['Sentence'])

# Create a TfidfVectorizer object to transform the documents into a document-term matrix
vectorizer = TfidfVectorizer(stop_words='english')

# Fit the TfidfVectorizer object to the documents and transform the documents into a document-term matrix
X = vectorizer.fit_transform(df['Sentence'])

# Define the number of clusters
num_clusters = len(categories)

# Create a KMeans object with the specified number of clusters
kmeans = KMeans(n_clusters=num_clusters)

# Fit the KMeans object to the document-term matrix
kmeans.fit(X)

# Evaluate the clustering performance
# This is optional but recommended to make sure the clustering is effective
labels_true = kmeans.labels_
score = adjusted_rand_score(labels_true, labels_true)
print("Clustering performance score: ", score)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/search")
def search_results():
    query = request.args.get("query")
    matches = search(query)
    return render_template("results.html", query=query, matches=matches)

@app.route("/cluster", methods=["GET", "POST"])
def cluster():
    if request.method == "POST":
        new_document = request.form["new_document"]
        print(new_document)
        new_document_matrix = vectorizer.transform([new_document])
        predicted_cluster = kmeans.predict(new_document_matrix)[0]
        predicted_category = categories[predicted_cluster]
        print(predicted_category)
        return render_template("clustering.html",new_document=new_document, predicted_category=predicted_category)
    else:
        return render_template("clustering_form.html")


if __name__ == '__main__':
    app.run(debug=True)