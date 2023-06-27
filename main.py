import re

import requests
from bs4 import BeautifulSoup

URL = "https://news.ycombinator.com"
DOWNLOAD_DIR = "/tmp"
CYCLE_SECONDS = 120 #sec


def find_news_blocks(url):
    blocks = []
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    news_headers = soup.findAll('tr', class_='athing')
    for tr in news_headers:
        comments_block = tr.findNextSibling('tr')
        comment_link = comments_block.find('a', string=re.compile('comment(s|)$'))
        news_link = tr.find('span', class_='titleline')
        news_link = news_link.a if news_link else None
        block = {'news_link': news_link['href'] if news_link else None,
                 'comment_link': (URL + '/' + comment_link['href']) if comment_link else None}
        blocks.append(block)
    return blocks


def main():
    all_news = find_news_blocks(URL)

    print(all_news)


if __name__ == '__main__':
    main()
