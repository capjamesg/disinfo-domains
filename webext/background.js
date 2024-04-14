var problematic_categories = ["pseudoscience"];

var problematic_category_regexes = [
    /mass media-related controversies/g,
];

function get_from_cache (url) {
    chrome.storage.local.get("misinformation_cache").then(function (data) {
        if (data.misinformation_cache == null) {
            return null;
        }
        var cache = JSON.parse(data.misinformation_cache);

        return cache[url];
    });
}

function save_to_cache (url, data) {
    chrome.storage.local.get("misinformation_cache").then(function (data) {
        var cache = {};

        if (data.misinformation_cache != null) {
            cache = JSON.parse(data.misinformation_cache);
        }

        cache[url] = data;

        chrome.storage.local.set({ misinformation_cache: JSON.stringify(cache) }, function () {
            console.log("Saved to cache");
        });
    });
}

function match_page_categories_against_problematic_categories(categories) {
    var problematic = false;

    for (var i = 0; i < categories.length; i++) {
        for (var j = 0; j < problematic_categories.length; j++) {
            if (categories[i].includes(problematic_categories[j])) {
                problematic = true;
            }
        }
    }

    for (var i = 0; i < problematic_category_regexes.length; i++) {
        for (var j = 0; j < categories.length; j++) {
            if (categories[j].match(problematic_category_regexes[i])) {
                problematic = true;
            }
        }
    }

    return problematic;
}

function get_categories(title) {
    if (get_from_cache(title) != null) {
        console.log("Using cache");
        var data = get_from_cache(title);
        var categories = data.categories;

        if (match_page_categories_against_problematic_categories(categories)) {
            chrome.action.setIcon({ path: "icon-yellow.png" });
        }
        return;
    }

    fetch("https://en.wikipedia.org/w/api.php?action=query&prop=revisions&titles=" + title + "&rvslots=*&rvprop=content&formatversion=2&format=json")
        .then(response => response.json())
        .then(data => {
            var page = data.query.pages[0];
            var is_missing = page.missing;
            if (is_missing) {
                // reset cache for current_page
                chrome.storage.local.set({ current_page: null }, function () {
                    console.log("Reset storage");
                });
                
                console.log("Page not found");
                return;
            }

            var page_data = page.revisions[0].slots.main.content;

            if (page_data.startsWith("#REDIRECT")) {
                var redirect_title = page_data.split("[[")[1].split("]]")[0];
                get_categories(redirect_title);
                return;
            }

            var categories = [];

            var category_regex = /\[\[Category:(.*?)\]\]/g;

            var match;

            while (match = category_regex.exec(page_data)) {
                categories.push(match[1]);
            }

            save_to_cache(title, { categories: categories });

            if (match_page_categories_against_problematic_categories(categories)) {
                chrome.action.setIcon({ path: "icon-yellow.png" });
            }

            // save categories ot "current_page" value
            chrome.storage.local.set({ current_page: JSON.stringify(categories) }, function () {
                console.log("Saved to storage");
            });
        })
        .catch(error => console.error('Error:', error));
}

chrome.tabs.onUpdated.addListener( function (tabId, changeInfo, tab) {
    // set page icon to icon-grey
    chrome.action.setIcon({ path: "icon-grey.png" });

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs.length === 0) return;
        var tab = tabs[0];
        var url = new URL(tab.url);

        console.log("URL: " + url);

        if (!url.protocol.startsWith('http:') && !url.protocol.startsWith('https:')) {
            console.log("Non-web page. Skipping...");
        } else {
            var domain = url.hostname;

            get_categories(domain);
        }
    });
});