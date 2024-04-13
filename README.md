# source-trust

This tool can be used for consulting the trustworthiness of a website given publicly available information.

This tool works by consulting Wikipedia to check if a website is assocaited with categories that may question the trustworthiness of a website (i.e. `Pseudoscience`), and looks up a website in publicly available, curated databases of websites associated with fake news.

This tool could be further extended to do lookups on attributes like domain ownership, affiliation with organizations known to be producers of untrustworthy content, and more.

## Example

Analysis of goop.com:

```
Website is flagged for the following reasons:
negative_sentiment_categories: Pseudoscience, Health fraud companies, Advertising and marketing controversies
````

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

- Wikipedia
- https://infogram.com/politifacts-fake-news-almanac-1gew2vjdxl912nj

## License

This project is licensed under an [MIT license](LICENSE).
