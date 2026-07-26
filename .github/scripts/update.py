#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime
from collections import defaultdict
import urllib.request

MONTH_EMOJIS = {
    1: '\U0001f305',   # 🌅 sunrise
    2: '\U0001f338',   # 🌸 cherry blossom
    3: '\U0001f33f',   # 🌿 herb
    4: '\U0001f30a',   # 🌊 wave
    5: '\U0001f304',   # 🌄 mountain sunrise
    6: '\U0001f333',   # 🌳 tree
    7: '\U0001f3d4\ufe0f',  # 🏔️ snow cap
    8: '\u2601\ufe0f', # ☁️ cloud
    9: '\U0001f343',   # 🍃 leaf
    10: '\U0001f33e',  # 🌾 sheaf of rice
    11: '\U0001f332',  # 🌲 evergreen
    12: '\u26f0\ufe0f', # ⛰️ mountain
}


def fetch_feed(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def parse_rss(xml_data):
    root = ET.fromstring(xml_data)
    ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
    items = []
    for item in root.findall('.//item'):
        title = item.findtext('title', '')
        link = item.findtext('link', '')
        pub_date_str = item.findtext('pubDate', '')
        description = item.findtext('description', '')

        content_el = item.find('content:encoded', ns)
        content = content_el.text if content_el is not None else description

        dt = parsedate_to_datetime(pub_date_str) if pub_date_str else None
        if dt is None:
            pub_date_dt = datetime.min
        else:
            pub_date_dt = dt.replace(tzinfo=None)

        items.append({
            'title': title.strip(),
            'link': link.strip(),
            'pubDate_dt': pub_date_dt,
            'content': content.strip(),
        })

    return sorted(items, key=lambda p: p['pubDate_dt'], reverse=True)


def format_date(pub_date_dt):
    if pub_date_dt == datetime.min:
        return ""
    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    day = pub_date_dt.day
    suffix = suffixes.get(day % 10, 'th') if day < 20 else 'th'
    return f"{day}{suffix} of {pub_date_dt.strftime('%B')} \U0001f3de\ufe0f"


def format_day(pub_date_dt):
    if pub_date_dt == datetime.min:
        return ""
    return f"{pub_date_dt.strftime('%a')}, {pub_date_dt.day}"


def time_ago(dt):
    if dt == datetime.min:
        return ""
    now = datetime.now()
    diff = now - dt
    days = diff.total_seconds() / 86400
    hours = diff.total_seconds() / 3600
    minutes = diff.total_seconds() / 60

    if days >= 1:
        return f"{int(days)} days"
    elif hours >= 1:
        return f"{int(hours)} hrs"
    else:
        return f"{int(minutes)} mins"


def generate_readme(posts):
    latest = posts[0] if posts else None

    readme = " "

    if latest:
        formatted_date = format_date(latest['pubDate_dt'])
        time_ago_str = time_ago(latest['pubDate_dt'])
        url = latest['link']
        content = latest['content']

        readme += f"""> [!important]
> > ##### **{formatted_date}**
>
> ### [`{latest['title']}`]({url})
>
> {content}
>
> > > > > > > > > > > > > > > > > >
"""

    remaining = posts[1:] if len(posts) > 1 else []

    if remaining:
        readme += "\n\n## \U0001f315 In case you missed it\n\n"

        by_year_month = defaultdict(lambda: defaultdict(list))
        for post in remaining:
            dt = post['pubDate_dt']
            if dt != datetime.min:
                by_year_month[dt.year][dt.month].append(post)

        for year in sorted(by_year_month.keys(), reverse=True):
            readme += f"### {year}\n\n"
            for month in sorted(by_year_month[year].keys(), reverse=True):
                month_name = datetime(year, month, 1).strftime('%B')
                month_emoji = MONTH_EMOJIS.get(month, '')
                readme += f"#### {month_name} {month_emoji}\n\n"
                for post in by_year_month[year][month]:
                    day_str = format_day(post['pubDate_dt'])
                    readme += f"- {day_str} - [{post['title']}]({post['link']})\n"
                readme += "\n"
    readme += f"""\

> [`iseeheaven`](https://github.com/iseeheaven) is a facet of [@prjctimg](https://github.com/prjctimg)
>
> Updated daily from RSS feed

"""
    return readme


def main():
    print("Fetching RSS feed...", file=sys.stderr)
    xml_data = fetch_feed("https://grdn.prjctimg.me/feed.xml")

    print("Parsing feed...", file=sys.stderr)
    posts = parse_rss(xml_data)

    print(f"Found {len(posts)} posts", file=sys.stderr)

    readme_content = generate_readme(posts)

    if len(sys.argv) > 1 and sys.argv[1] == "--write":
        with open("README.md", "w") as f:
            f.write(readme_content)
        print("README.md updated!", file=sys.stderr)
    else:
        print(readme_content)


if __name__ == "__main__":
    main()
