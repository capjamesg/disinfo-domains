# Source Trust

This tool can be used for consulting the trustworthiness of a website given publicly available information.

This tool works by consulting Wikipedia to check if a website is assocaited with categories that may question the trustworthiness of a website (i.e. `Pseudoscience`), and looks up a website in publicly available, curated databases of websites associated with fake news.

This tool could be further extended to do lookups on attributes like domain ownership, affiliation with organizations known to be producers of untrustworthy content, and more.

## Getting Started

First, install the project from PyPi:

```bash
pip install 
```

Then, you can use the tool as follows:

```python
from source_trust import generate_report


DOMAIN = "ABCNews.com.co"
report = generate_report(DOMAIN.lower())

if any(len(value) > 0 for value in report.values()):
    print("Website is flagged for the following reasons:")
    for key, value in report.items():
        if key == "all_categories":
            continue

        if len(value) > 0:
            print(key + ": " + ", ".join(value))
else:
    print("Website is not flagged")
```

## Path of a Request

Source Trust completes several steps to determine the trustworthiness of a website.

First, Source Trust opens the cache of the day. This cache includes:

1. The categories from all previous requests made that day.
2. The known problematic websites listed on Wikipedia's untrustworthy websites lists retrieved that day.

If the site has not yet been retrieved, it is retrieved and categories are extracted from the wiki page.

If the site has been retrieved, the categories are extracted from the cache.

Next, the following checks take place:

1. If the site is in the known problematic websites list, it is flagged.
2. If the site has any negative sentiment categories, a consensus algorithm is run. This algorithm uses cached categories from the last `N` days, if available, to determine if any problematic categories are consistent across multiple days. There are four options available:
    - `percent`: The percentage of days the category was present in the last `N` days.
    - `majority`: The category was present in the majority of the last `N` days.
    - `unanimous`: The category was present in all of the last `N` days.
    - `in_one_or_more`: The category was present in one or more of the last `N` days.
3. If the consensus algorithm finds a category or set of categories that meet the specified consensus method, the site is flagged.
4. If the consensus algorithm does not have enough data (i.e. there are not enough days in the cache), the site is flagged if it has any negative sentiment categories.

Negative sentiment is determined using a pre-trained sentence classifier available on Hugging Face.

The consensus algorithm is implemented to prevent against spam or malicious edits on Wikipedia compromising the integrity of the tool. For example, if a reputable site is given a negative sentiment category on Wikipedia (i.e. Pseudoscience), the consensus algorithm will prevent the site from being flagged as untrustworthy.

This only works if there is at least one day of data available in the cache. If there is no data available, the site will be flagged as untrustworthy if it has any negative sentiment categories.

To counter this, any extension using this tool should consider showing all categories to users directly, allowing people to make their own decisions about the trustworthiness of a site.

## Limitations

Trust is considered at the level of the domain. Thus, using this tool one could derive that `example.com` is trustworthy, but not specifically `example.com/example`.

Trust is not analyzed at the subdomain level, unless a subdomain is specifically logged in a database used by this tooland noted as untrustworthy. Thus, if `example.com` is considered trustworthy, `example.example.com` would not have a ranking unless it were logged in a database used by this tool and noted as untrustworthy.

This tool is not meant to be a substitute to analyzing source material to verify the veracity and reliability of information in an article.

## Example

Analysis of goop.com:

```
Website is flagged for the following reasons:
negative_sentiment_categories: Pseudoscience, Health fraud companies, Advertising and marketing controversies
```

Analysis of wordpress.com:

```
Website is not flagged.
```

Analysis of abcnews.com.co:

```
Website is flagged for the following reasons:
negative_sentiment_categories: Fake news websites, Defunct websites
known_problematic_websites: abcnews.com.co
```

## Lists Consulted for Reliability Checks

See the `KNOWN_LISTS` variable in `source_trust.py` for a list of lists consulted for reliability checks.

## Contributing

Have an idea on how this project can be better? Leave an Issue on the [project GitHub repository](https://github.com/capjamesg/source-trust). Want to contribute? Fork the project and make a pull request.

## License

This project is licensed under an [MIT license](LICENSE).