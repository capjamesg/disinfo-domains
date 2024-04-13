import re
import warnings

# suppress UserWarning from Transformers
warnings.filterwarnings("ignore")

from urllib.parse import urlparse

import pandas as pd
import requests
import torch
import validators
from transformers import AutoModelForSequenceClassification, AutoTokenizer


tokenizer = AutoTokenizer.from_pretrained("stevhliu/my_awesome_model")
model = AutoModelForSequenceClassification.from_pretrained("stevhliu/my_awesome_model")

CATEGORIES_TO_FLAG = {
    "Satire": [
        re.compile(r"Satire", re.IGNORECASE),
        re.compile(r"Satirical", re.IGNORECASE),
    ],
}

# url2table heading
KNOWN_LISTS = {"https://en.wikipedia.org/wiki/List_of_fake_news_websites": "Domain"}


def extract_categories(content: str) -> list:
    """
    Extract all categories from a Wikipedia page.

    :param content: The content of the Wikipedia page.
    :return: A list of categories.
    """
    categories = re.findall(r"\[\[Category:(.*?)\]\]", content)

    categories = [re.sub(r"\|.*", "", category) for category in categories]

    return categories


def extract_known_problematic_websites(url: str) -> list:
    """
    Extract known problematic websites from a specified Wikipedia page.

    :param url: The URL of the Wikipedia page.
    :return: A list of known problematic websites.
    """

    heading = KNOWN_LISTS[url]
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    tables = pd.read_html(response.text)
    flat_table = pd.concat(tables)
    result = flat_table[heading].tolist()
    # remove [.com] and nan
    result = [x.replace("[.]", ".") for x in result if isinstance(x, str)]
    return result


def get_wiki_page(title: str):
    """
    Get the content of a Wikipedia page.

    :param title: The title of the Wikipedia page.
    :return: The content of the Wikipedia page.
    """

    url = (
        "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles="
        + title
        + "&rvslots=*&rvprop=content&formatversion=2&format=json"
    )
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})

    response_code = response.status_code

    if response_code != 200:
        return None, response_code

    if "missing" in response.json()["query"]["pages"][0]:
        return None, 404

    content = response.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]

    if content.startswith("#REDIRECT"):
        text = re.search(r"\[\[(.*?)\]\]", content).group(1)

        if "#" in text:
            text = text.split("#")[0]

        return get_wiki_page(text)

    return content, response_code


def get_sentiment(text: str) -> str:
    """
    Get the sentiment of a category.

    :param text: The text to get the sentiment for.
    :return: The sentiment of the text.
    """

    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = torch.argmax(logits).item()
    id2label = model.config.id2label[predicted_class_idx]
    # if LABEL_1 or confidence of LABEL_0 < 0.8
    return "positive" if id2label == "LABEL_1" or torch.softmax(logits, dim=1)[0][0] < 0.8 else "negative"


def generate_report(url: str) -> dict:
    """
    Generate a report for a given URL.

    The report contains the following:
    
    - Flagged categories
    - Negative sentiment categories
    - Known problematic websites

    :param url: The URL to generate a report for.
    :return: A dictionary containing the report.
    """

    if not validators.url(url):
        url = "https://" + url

    domain = urlparse(url).netloc

    if domain.startswith("www."):
        domain = domain[4:]

    domain = domain.strip()

    result, status_code = get_wiki_page(domain)

    if status_code == 404:
        print("Page not found")
        exit()

    categories = extract_categories(result)
    sentiments = {category: get_sentiment(category) for category in categories}

    report = {"flagged_categories": [], "negative_sentiment_categories": [], "known_problematic_websites": []}

    if any(sentiment == "negative" for sentiment in sentiments.values()):
        report["negative_sentiment_categories"] = [
            category for category, sentiment in sentiments.items() if sentiment == "negative"
        ]

    for site in KNOWN_LISTS.items():
        if any(domain in extract_known_problematic_websites(site) for domain in sentiments.keys()):
            report["known_problematic_websites"] = [
                domain for domain in sentiments.keys() if domain in extract_known_problematic_websites(site)
            ]

    for category, regexes in CATEGORIES_TO_FLAG.items():
        for regex in regexes:
            if any(regex.search(category) for category in categories):
                report["flagged_categories"].append(category)

    return report


DOMAIN = "https://wordpress.com"
report = generate_report(DOMAIN)

if any(len(value) > 0 for value in report.values()):
    print("Website is flagged for the following reasons:")
    for key, value in report.items():
        if len(value) > 0:
            print(key + ": " + ", ".join(value))
else:
    print("Website is not flagged")
