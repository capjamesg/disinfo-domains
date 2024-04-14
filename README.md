# Disinformation Domains

[![version](https://badge.fury.io/py/disinfo-domains.svg?)](https://badge.fury.io/py/disinfo-domains)
[![downloads](https://img.shields.io/pypi/dm/disinfo-domains)](https://pypistats.org/packages/disinfo-domains)
[![license](https://img.shields.io/pypi/l/disinfo-domains?)](https://github.com/capjamesg/disinfo-domains/blob/main/LICENSE)
[![python-version](https://img.shields.io/pypi/pyversions/disinfo-domains)](https://badge.fury.io/py/disinfo-domains)

Look up whether a domain is listed in a category associated with disinformation or fake news on Wikipedia.

This tool also consults Wikipedia lists of websites known to be associated with fake news.

## Getting Started

First, install the project from PyPi:

```bash
pip install disinfo-domains
```

Then, you can use the tool as follows:

```python
from disinfo_domains import generate_report


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

This package completes several steps to determine whether Wikipedia reports a site has been associated with disinformation.

First, this tool opens the cache of the day. This cache includes:

1. The categories from all previous requests made that day.
2. The known problematic websites listed on Wikipedia's disinformation websites lists retrieved that day.

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

The consensus algorithm is implemented to prevent against spam or malicious edits on Wikipedia compromising the integrity of the tool. For example, if a reputable site is given a negative sentiment category on Wikipedia (i.e. Pseudoscience), the consensus algorithm will prevent the site from being flagged as potentially spreading disinformation.

This only works if there is at least one day of data available in the cache. If there is no data available, the site will be flagged as potentially spreading disinformation if it has any negative sentiment categories.

To counter this, any extension using this tool should consider showing all categories to users directly, allowing people to make their own decisions about a website.

## Limitations

This tool works at the level of the domain. Thus, using this tool one could derive that `example.com` spreads fake news, but not specifically `example.com/example`.

This project is not specifically analyzed at the subdomain level, unless a subdomain is logged on Wikipedia as potentially spreading fake news. Thus, if `example.com` has no ranking, `example.example.com` would not have a ranking either it were logged in a database used by this tool and noted as potentially spreading disinformation.

This tool is not meant to be a substitute to analyzing source material to verify the veracity and reliability of information in an article. It only looks up whether a domain has been listed as being associated with disinformation on Wikipedia.

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

See the `KNOWN_LISTS` variable in `disinfodomains/disinfodomains.py` for a list of lists consulted for reliability checks.

## Contributing

Have an idea on how this project can be better? Leave an Issue on the [project GitHub repository](https://github.com/capjamesg/disinfo-domains). Want to contribute? Fork the project and make a pull request.

## License

This project is licensed under an [MIT license](LICENSE).