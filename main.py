import os
import re
import uuid

import requests
from bs4 import BeautifulSoup

URL = "https://news.ycombinator.com"
DOWNLOAD_DIR = "/tmp/ycrawler"
CYCLE_SECONDS = 120 #sec


def create_dir(dir_name):
    path = DOWNLOAD_DIR + dir_name
    if not os.path.exists(path):
        os.makedirs(path)


def write_to_file(filename, content):
    f = open(filename, "w")
    f.write(content)
    f.close()


def generate_name_from_link(url):
    return "/" + str(uuid.uuid4())


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
        news_link = news_link['href'] if news_link else None
        if news_link is not None and 'http' != news_link[:4]:
            news_link = URL + '/' + news_link

        block = {'news_link': news_link,
                 'comment_link': (URL + '/' + comment_link['href']) if comment_link else None}
        blocks.append(block)
    return blocks


def get_content(url):
    response = requests.get(url)
    content = response.content.decode('utf-8')
    return content


def main():
    all_news = find_news_blocks(URL)
    for news in all_news:
        news_link = news['news_link']
        if news_link:
            dir_name = generate_name_from_link(news_link)
            content = get_content(news_link)
            create_dir(dir_name)
            filename = DOWNLOAD_DIR + dir_name + dir_name + '.html'
            write_to_file(filename, content)


if __name__ == '__main__':
    main()
