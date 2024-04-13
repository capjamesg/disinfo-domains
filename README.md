# Source Trust

This tool can be used for consulting the trustworthiness of a website given publicly available information.

This tool works by consulting Wikipedia to check if a website is assocaited with categories that may question the trustworthiness of a website (i.e. `Pseudoscience`), and looks up a website in publicly available, curated databases of websites associated with fake news.

This tool could be further extended to do lookups on attributes like domain ownership, affiliation with organizations known to be producers of untrustworthy content, and more.

## Limitations

Trust is considered at the level of the domain. Thus, using this tool one could derive that `example.com` is trustworthy, but not specifically `example.com/example`.

Trust is not analyzed at the subdomain level, unless a subdomain is specifically logged in a database used by this tooland noted as untrustworthy. Thus, if `example.com` is considered trustworthy, `example.example.com` would not have a ranking unless it were logged in a database used by this tool and noted as untrustworthy.

This tool is not meant to be a substitute to analyzing source material to verify the veracity and reliability of information in an article.

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

- [Wikipedia fake news website list](https://en.wikipedia.org/wiki/List_of_fake_news_websites)
- [Infogram fake news website list](https://infogram.com/politifacts-fake-news-almanac-1gew2vjdxl912nj)

## License

This project is licensed under an [MIT license](LICENSE).
