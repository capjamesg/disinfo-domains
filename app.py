import re

import requests
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DOMAIN = "google.com"

tokenizer = AutoTokenizer.from_pretrained("stevhliu/my_awesome_model")
model = AutoModelForSequenceClassification.from_pretrained("stevhliu/my_awesome_model")

def extract_categories(content):
    categories = re.findall(r"\[\[Category:(.*?)\]\]", content)
    return categories


def get_wiki_page(title):
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles="
        + title
        + "&rvslots=*&rvprop=content&formatversion=2&format=json"
    )
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    content = response.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]

    if content.startswith("#REDIRECT"):
        return get_wiki_page(re.search(r"\[\[(.*?)\]\]", content).group(1))

    return content

def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = torch.argmax(logits).item()
    id2label = model.config.id2label[predicted_class_idx]
    return "positive" if id2label == "LABEL_1" else "negative"

result = get_wiki_page(DOMAIN)
categories = extract_categories(result)
sentiments = {category: get_sentiment(category) for category in categories}

print(sentiments)
