#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
from collections import defaultdict
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

with open('keyword_labels.json', 'r') as f:
    keyword_labels = json.load(f)

def infer_label(title):
    title_lower = title.lower()
    for keyword, label in keyword_labels.items():
        if keyword in title_lower:
            return label
    return None

def CategoryClustering(rss_data): # TYPE: {title: string, url: srting}
    df = pd.DataFrame([rss_data])

    # Load sentence transformer for embeddings
    embeddings = model.encode(df['title'].tolist())

    # Choose number of clusters (e.g., try 10 for starters)
    # num_clusters = 10
    kmeans = KMeans(n_clusters=1, random_state=42)
    df['cluster'] = kmeans.fit_predict(embeddings)

    # Map each title to a label using keyword hints
    inferred = infer_label(df['title'].iloc[0])
    if inferred is None:
        return None

    return {"title": df['title'].iloc[0], "category": inferred, "url": df['url'].iloc[0]}


# Categories extraction (Indian Express)
url = "https://indianexpress.com/rss/"
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

rss_feed_div = soup.find("div", class_="rss-feed")

categorized_links = defaultdict(list)

if rss_feed_div:
    rows = rss_feed_div.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            category = cols[0].get_text(strip=True)
            link_tag = cols[1].find("a", href=True)
            if link_tag and category:
                result = CategoryClustering({
                    "title": category,
                    "url": link_tag['href']
                })
                if result:
                    cat = result['category']
                    if len(categorized_links[cat]) < 5:
                        categorized_links[cat].append(result)

rss_links = [item for sublist in categorized_links.values() for item in sublist]
print(json.dumps(rss_links, indent=2))

# categories = CategoryClustering(rss_links)
# print(rss_links)
