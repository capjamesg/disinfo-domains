var problematic_categories = ["pseudoscience"];

var problematic_category_regexes = [
    /mass media-related controversies/g,
];

function match_page_categories_against_problematic_categories(categories) {
    var problematic = false;

    for (var i = 0; i < categories.length; i++) {
        for (var j = 0; j < problematic_categories.length; j++) {
            if (categories[i].toLowerCase().includes(problematic_categories[j])) {
                problematic = true;
            }
        }
    }

    for (var i = 0; i < problematic_category_regexes.length; i++) {
        for (var j = 0; j < categories.length; j++) {
            if (categories[j].toLowerCase().match(problematic_category_regexes[i])) {
                problematic = true;
            }
        }
    }

    return problematic;
}

chrome.storage.local.get('current_page', function(data) {
    var page = JSON.parse(data.current_page);
    console.log(page, "page");
    for (var i = 0; i < page.length; i++) {
        var item = page[i];
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.href = "https://en.wikipedia.org/wiki/" + item;
        a.target = "_blank";
        a.textContent = item;
        // give .warning category if it's problematic
        if (match_page_categories_against_problematic_categories([item])) {
            li.classList.add('warning');
        }

        li.appendChild(a);
        
        document.getElementById('categories').appendChild(li);
    }
});