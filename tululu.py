import requests
import os
import pathvalidate
import bs4
import urllib.parse
import json
import sys
import argparse
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', type=int, default=1)
    parser.add_argument('--end_page', type=int, default=sys.maxsize**10)
    return parser


def get_book_title(books_soup):
    title_and_author_selector = "#content h1"
    title_and_author = books_soup.select_one(title_and_author_selector).text.split("::")
    book_title = title_and_author[0].strip()
    return book_title


def get_book_author(books_soup):
    title_and_author_selector = "#content h1"
    title_and_author = books_soup.select_one(title_and_author_selector).text.split("::")
    book_author = title_and_author[1].strip()
    return book_author


def download_txt(folder, book_title):
    book_file_extension = ".txt"
    book_id = book_url.split('/')[-2].split('b')[1]
    txt_url_template = "txt.php?id={}".format(book_id)
    txt_url = urljoin(url, txt_url_template)
    os.makedirs(folder, exist_ok=True)
    response = requests.get(txt_url, allow_redirects=False)

    if response.status_code == 200:
        book_filename = sanitize_filename("{}{}".format(book_title,book_file_extension))
        book_path = os.path.join(folder, book_filename)
        with open(book_path, 'wb') as file:
            file.write(response.content)
        return book_path


def download_image(folder, books_soup):
    image_link_selector = ".bookimage a img"
    img_src = books_soup.select_one(image_link_selector)['src']
    image_link = urljoin(url, img_src)
    image_name = img_src.split('/')[2]
    os.makedirs(folder, exist_ok=True)
    response = requests.get(image_link, allow_redirects=False)
    response.raise_for_status()

    image_path = os.path.join(folder, sanitize_filename(image_name))
    with open(image_path, 'wb') as file:
        file.write(response.content)
    return image_path


def create_json_catalogue(json_catalogue):
    with open(json_catalogue, "w", encoding='utf8') as my_file:
        json.dump(books_catalogue,my_file, indent="   ",ensure_ascii=False)


def get_comments(books_soup):
    comments_selector = ".texts .black"
    comments_blocks = books_soup.select(comments_selector)
    comments = [comment.text for comment in comments_blocks]
    return comments


def get_genres(books_soup):
    genres_selector = "span.d_book a"
    genres_blocks = books_soup.select(genres_selector)
    genres = [genre.text for genre in genres_blocks]
    return genres


def link_checker(page_url):
    page_response = requests.get(page_url, allow_redirects=False)
    if page_response.status_code == 200:
        return page_response
    else:
        exit()



if __name__ == "__main__":
    load_dotenv()
    books_folder = os.getenv('BOOKS_FOLDER')
    images_folder = os.getenv('IMAGES_FOLDER')
    json_catalogue = os.getenv('JSON_CATALOGUE')

    url = 'http://tululu.org'
    books_catalogue = []
    parser_args = create_parser().parse_args()

    for page_num in range(parser_args.start_page, parser_args.end_page):
        page_url_template = 'l55/{page_num}/'.format(page_num=page_num)
        page_url = urljoin(url, page_url_template)
        page_response = link_checker(page_url)
        page_soup = BeautifulSoup(page_response.text, 'lxml')

        books_selector = ".bookimage a"
        books_blocks = page_soup.select(books_selector)

        for book in books_blocks:
            book_url = urljoin(url, book['href'])

            response = requests.get(book_url, allow_redirects=False)
            response.raise_for_status()


            books_soup = BeautifulSoup(response.text, 'lxml')

            book_title = get_book_title(books_soup)
            img_src = download_image(os.path.join(images_folder), books_soup)
            book_path = download_txt(os.path.join(books_folder), book_title)

            books_characteristics = {'title': book_title,
                                     'author': get_book_author(books_soup),
                                     'img_src': img_src,
                                     'book_path': book_path,
                                     'comments': get_comments(books_soup),
                                     'genres': get_genres(books_soup),
                                     }


            books_catalogue.append(books_characteristics)

        create_json_catalogue(json_catalogue)