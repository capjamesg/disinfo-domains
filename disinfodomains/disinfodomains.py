import datetime
import json
import os
import re
import warnings

# suppress UserWarning from Transformers
warnings.filterwarnings("ignore")

import csv
from urllib.parse import urlparse

import pandas as pd
import requests
import torch
import validators
from transformers import AutoModelForSequenceClassification, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("stevhliu/my_awesome_model")
model = AutoModelForSequenceClassification.from_pretrained("stevhliu/my_awesome_model")

SENTIMENT_CLASSIFIER_CONFIDENCE = 0.8
CONSENSUS_STRATEGY = "in_one_or_more"
USER_AGENT = "Mozilla/5.0; disinfo-domains/0.1"

CATEGORIES_TO_FLAG = {
    "Satire": [
        re.compile(r"Satire", re.IGNORECASE),
        re.compile(r"Satirical", re.IGNORECASE),
    ],
}

# url2table heading
KNOWN_LISTS = {
    "https://en.wikipedia.org/wiki/List_of_fake_news_websites": "Domain",
    "https://en.wikipedia.org/wiki/List_of_miscellaneous_fake_news_websites": "Domain",
    "https://en.wikipedia.org/wiki/List_of_corporate_disinformation_website_campaigns": "Domain",
    "https://en.wikipedia.org/wiki/List_of_political_disinformation_website_campaigns_in_the_United_States": "Domain",
    "https://en.wikipedia.org/wiki/List_of_political_disinformation_website_campaigns": "Domain",
    "https://en.wikipedia.org/wiki/List_of_satirical_fake_news_websites": "Domain",
    "https://en.wikipedia.org/wiki/List_of_fake_news_troll_farms": "Domain",
}
KNOWN_CSV_LISTS = {}

CACHE_DIRECTORY = ".disinfo-domains/cache"  # os.path.join("~", ".disinfo-domains", "cache")

os.makedirs(CACHE_DIRECTORY, exist_ok=True)

global active_cache
global active_cache_day

active_cache_day = None
active_cache = {}


def get_day_cache(day=datetime.datetime.now().strftime("%Y-%m-%d")):
    """
    Retrieve the cache for a specific day.

    If the cache does not exist, an empty dictionary will be returned.

    If the cache exists, the cache will be returned.

    If the cache is for today, the active cache will be returned.

    Args:
        day: The day to retrieve the cache for.

    Returns:
        The cache for the specified day.
    """
    print("Reading cache for", day)

    global active_cache
    global active_cache_day

    # check active cache for today
    if active_cache_day == datetime.datetime.now().strftime(
        "%Y-%m-%d"
    ) and day == datetime.datetime.now().strftime("%Y-%m-%d"):
        return active_cache

    print("Reading cache for", day, "from file")

    cache_file = os.path.join(CACHE_DIRECTORY, day + ".json")
    active_cache_day = datetime.datetime.now().strftime("%Y-%m-%d")

    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

    return {}


def save_to_cache(cache, data, key, day=datetime.datetime.now().strftime("%Y-%m-%d")):
    """
    Save a value to the cache.

    This function will set a value in the cache if the value does not exist, or merge the value with the existing value.

    Merging is supported specifically because this package only deals with flat lists of items.

    Args:
        cache: The cache to save the value to.
        data: The data to save.
        key: The key to save the data under.
        day: The day to save the data under.

    Returns:
        None
    """
    cache_file = os.path.join(CACHE_DIRECTORY, day + ".json")

    if key not in cache:
        cache[key] = data
    else:
        cache[key] = list(set(cache[key] + data))

    with open(cache_file, "w") as f:
        json.dump(cache, f)

    global active_cache
    global active_cache_day

    active_cache = cache
    active_cache_day = day


def get_consensus(
    domain: str,
    n: int = 3,
    consensus_strategy: str = "in_one_or_more",
    consensus: float = 0.75,
):
    """
    Check for a consensus of categories.

    This function will retrieve the categories for the last n days and check for a consensus of categories.

    The following strategies are supported:

    - percent: A percentage of the days must have the category.
    - majority: A majority of the days must have the category.
    - unanimous: All days must have the category.
    - in_one_or_more: The category must be in one or more days.

    Args:
        domain: The domain to check for.
        n: The number of days to check.
        consensus_strategy: The strategy to use.
        consensus: The consensus threshold.

    Returns:
        A list of problematic categories.
    """
    days = [datetime.datetime.now().strftime("%Y-%m-%d")]

    if n == 1:
        return get_day_cache()[domain]

    for num in range(1, n):
        days.append(
            (datetime.datetime.now() - datetime.timedelta(days=num)).strftime(
                "%Y-%m-%d"
            )
        )

    categories = [get_day_cache(day).get(domain, []) for day in days]

    category_count = {}

    for day in categories:
        for category in day:
            if category not in category_count:
                category_count[category] = 1
            else:
                category_count[category] += 1

    problematic_categories = []

    if consensus_strategy == "percent":
        for category, count in category_count.items():
            if count >= n * consensus:
                problematic_categories.append(category)
    elif consensus_strategy == "majority":
        for category, count in category_count.items():
            if count >= n / 2:
                problematic_categories.append(category)
    elif consensus_strategy == "unanimous":
        for category, count in category_count.items():
            if count == n:
                problematic_categories.append(category)
    elif consensus_strategy == "in_one_or_more":
        for category, count in category_count.items():
            if count >= 1:
                problematic_categories.append(category)

    return problematic_categories


def extract_categories(content: str) -> list:
    """
    Extract all categories from a Wikipedia page.

    Args:
        content: The content of the Wikipedia page.

    Returns:
        A list of categories.
    """
    categories = re.findall(r"\[\[Category:(.*?)\]\]", content)

    categories = [re.sub(r"\|.*", "", category) for category in categories]

    return categories


def extract_known_problematic_websites(cache: str, url: str) -> list:
    """
    Extract known problematic websites from a specified Wikipedia page.

    Args:
        cache: The cache to use.
        url: The URL of the Wikipedia page.

    Returns:
        A list of known problematic websites.
    """

    heading = KNOWN_LISTS[url]

    if url in cache:
        result = cache["known_problematic_websites"]
    else:
        last_modified = cache.get("last_modified", {}).get(url, None)

        headers = {"User-Agent": USER_AGENT}

        if last_modified:
            headers["If-Modified-Since"] = last_modified

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=10,
            )
        except requests.exceptions.RequestException as e:
            print("Error fetching", url, e)
            return []

        if not cache.get("last_modified"):
            cache["last_modified"] = {}

        cache["last_modified"][url] = response.headers.get("Last-Modified", None)

        if response.status_code == 304:
            result = cache.get("known_problematic_websites", [])
            save_to_cache(cache, result, "known_problematic_websites")
            return result

        tables = pd.read_html(response.text)
        flat_table = pd.concat(tables)
        result = flat_table[heading].tolist()
        # remove [.com] and nan
        result = [x.replace("[.]", ".").lower() for x in result if isinstance(x, str)]

    save_to_cache(cache, result, "known_problematic_websites")
    return result


def extract_known_problematic_websites_csv(csv_file: str) -> list:
    """
    Extract known problematic websites from a specified CSV file.

    This is not used, but may be useful in scenarios where you want to restrict websites you have identified as problematic.

    Args:
        csv_file: The path to the CSV file.

    Returns:
        A list of known problematic websites.
    """

    heading = KNOWN_CSV_LISTS[csv_file]
    # header row is always the first row
    with open(csv_file, newline="") as f:
        reader = csv.reader(f)
        data = list(reader)
    data[0] = [x.replace('"', "").strip() for x in data[0]]
    data[0] = [x.replace("\ufeff", "") for x in data[0]]

    flat_table = pd.DataFrame(data[1:], columns=data[0])
    flat_table = flat_table.apply(lambda x: x.str.lower() if x.dtype == "object" else x)

    result = flat_table[heading].tolist()
    # remove [.com] and nan
    result = [x.replace("[.]", ".") for x in result if isinstance(x, str)]
    return result


def get_wiki_page(title: str):
    """
    Get the content of a Wikipedia page.

    This strategy is taken since the Wikipedia Categories API returns the category
    associated with a redirect, not the page to which the redirects -- which may
    involve one or more hops -- point.

    Args:
        title: The title of the Wikipedia page.

    Returns:
        The content of the Wikipedia page.
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

    content = response.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"][
        "content"
    ]

    if content.startswith("#REDIRECT"):
        text = re.search(r"\[\[(.*?)\]\]", content).group(1)

        if "#" in text:
            text = text.split("#")[0]

        return get_wiki_page(text)

    return content, response_code


def get_sentiment(text: str) -> str:
    """
    Get the sentiment of a category.

    Args:
        text: The text to get the sentiment of.

    Returns:
        The sentiment of the text.
    """

    inputs = tokenizer(text, return_tensors="pt")
    outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_idx = torch.argmax(logits).item()
    id2label = model.config.id2label[predicted_class_idx]
    # if LABEL_1 or confidence of LABEL_0 < 0.8
    return (
        "positive"
        if id2label == "LABEL_1"
        or torch.softmax(logits, dim=1)[0][0] < SENTIMENT_CLASSIFIER_CONFIDENCE
        else "negative"
    )


def generate_report(url: str, consensus = True) -> dict:
    """
    Generate a report for a given URL.

    The report contains the following:

    - Flagged categories
    - Negative sentiment categories
    - Known problematic websites

    Args:
        url: The URL to generate the report for.
        consensus: Whether to use a consensus strategy.

    Returns:
        A dictionary containing the report.

    Example:
        ```python
            >>> generate_report("https://www.abcnews.com.co")
            {
                "flagged_categories": [],
                "negative_sentiment_categories": [],
                "known_problematic_websites": [],
                "all_categories": []
            }
        ```
    """

    if not validators.url(url):
        url = "https://" + url

    domain = urlparse(url).netloc

    if domain.startswith("www."):
        domain = domain[4:]

    domain = domain.strip()

    report = {
        "flagged_categories": [],
        "negative_sentiment_categories": [],
        "known_problematic_websites": [],
        "all_categories": [],
    }

    # if domain is in cache, return it
    cache = get_day_cache()

    if domain in cache:
        result, status_code = None, 200

    result, status_code = get_wiki_page(domain)

    if status_code != 404:
        if domain in cache:
            categories = cache[domain]
        else:
            categories = extract_categories(result)

        sentiments = {category: get_sentiment(category) for category in categories}

        report["all_categories"] = categories

        if any(sentiment == "negative" for sentiment in sentiments.values()):
            negative_sentiment_categories_today = [
                category
                for category, sentiment in sentiments.items()
                if sentiment == "negative"
            ]

            save_to_cache(cache, negative_sentiment_categories_today, domain)

            if consensus:
                consensus_report = get_consensus(domain, consensus_strategy=CONSENSUS_STRATEGY)

                report["negative_sentiment_categories"] = consensus_report
            else:
                report["negative_sentiment_categories"] = negative_sentiment_categories_today

        for site in KNOWN_LISTS.keys():
            if any(
                domain in extract_known_problematic_websites(cache, site)
                for domain in sentiments.keys()
            ):
                report["known_problematic_websites"].extend(
                    [
                        domain
                        for domain in sentiments.keys()
                        if domain in extract_known_problematic_websites(cache, site)
                    ]
                )

        for category, regexes in CATEGORIES_TO_FLAG.items():
            for regex in regexes:
                if any(regex.search(category) for category in categories):
                    report["flagged_categories"].append(category)

    for site in KNOWN_CSV_LISTS.keys():
        if any(
            domain in extract_known_problematic_websites_csv(site)
            for domain in [domain]
        ):
            report["known_problematic_websites"].extend(
                [
                    domain
                    for domain in [domain]
                    if domain in extract_known_problematic_websites_csv(site)
                ]
            )

    return report
