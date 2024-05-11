import logging
import redis.exceptions
import requests
import redis
import os

from bs4 import BeautifulSoup, Tag
from src import config
from src.product import Product
from src.storage import Storage


logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
IMAGES_PATH = "resources/images/"


# configure proxy for requests
PROXIES = {}
if config.PROXY:
    if config.PROXY.startswith("http:"):
        PROXIES["http"] = config.PROXY
    elif config.PROXY.startswith("https:"):
        PROXIES["http"] = config.PROXY
    else:
        logging.warning(f"Invalid proxy {config.PROXY}. PROXY config should starts with http or https.")


# connect to redis for cache
try:
    cache = redis.Redis(host='scrap_redis', port=6379, decode_responses=True)
    cache.ping()
    logging.info("Connected to redis for caching.")
except redis.exceptions.ConnectionError as err:
    logging.error("Failed to connect with redis for caching. continuing without cache.")
    cache = None


class DentalStall:
    DENTAL_STALL_URL: str = "https://dentalstall.com/shop/page/{}/"
    DENTAL_STALL_HEADERS: dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }

    def __init__(self) -> None:
        self.products: dict[str, Product] = {}
        self.updated_in_db: int = 0
        self.scraped_with_image: int = 0
        self.parsed_products: int = 0
        os.makedirs(IMAGES_PATH, exist_ok=True)

    def parse_page(self, nth_page: int) -> None:
        logging.info(f"Fetching page {nth_page}...")
        try:
            html_code = self.fetch_page(nth_page)
        except requests.exceptions.ProxyError as err:
            logging.error(f"Failed to connect to {config.PROXY} proxy.")
            return

        logging.info(f"Parsing page {nth_page}...")
        self._parse_page_html(html_code)
        logging.info(f"Completed page {nth_page}.")

    def fetch_page(self, page_number: int) -> str:
        response = requests.get(
            self.DENTAL_STALL_URL.format(page_number),
            headers=self.DENTAL_STALL_HEADERS,
            proxies=PROXIES
        )
        return response.text

    def _to_product(self, product_details: dict[str, str]) -> str:
        image_url = product_details.pop("image_url")
        file_name = product_details.get("sku") + "." + image_url.split(".")[-1]
        response = requests.get(image_url, proxies=PROXIES)
        if response.status_code == 200:
            file_path = IMAGES_PATH + file_name
            with open(file_path, "wb") as f:
                f.write(response.content)
            product_details["image_path"] = file_path
            return Product(**product_details)
        else:
            logging.warning(f"Failed to download image for {product_details.get('sku')} from image_url.")
            return None

    def _parse_product(self, item_tag: Tag) -> Product:
        thumbnail_tag = item_tag.select_one(".mf-product-thumbnail > a")
        item_title_tag = item_tag.select_one(".mf-product-content > h2")

        item_details_tag = item_tag.select_one(".mf-product-details")
        item_price_tag = item_details_tag.select_one(".price")
        if item_price_tag and item_price_tag.select_one("bdi"):
            item_price_tag = item_price_tag.select_one("bdi")
            if item_price_tag and item_price_tag.find("span"): item_price_tag.span.decompose()

        item_other_tag = item_details_tag.select_one(".mf-product-price-box > .addtocart-buynow-btn > a")

        item_title = item_title_tag and item_title_tag.text.strip().encode("ascii", "ignore").decode()
        item_price = item_price_tag and item_price_tag.text.strip().encode("ascii", "ignore").decode()
        item_image_src = thumbnail_tag.select_one("img").get("data-lazy-src")
        # item_src = thumbnail_tag and thumbnail_tag.get("href")
        item_sku = item_other_tag and item_other_tag.get("data-product_sku").strip()
        return {
            "sku": item_sku,
            "price": item_price,
            "title": item_title,
            "image_url": item_image_src
        }

    def _parse_page_html(self, html_code: str) -> None:
        soup = BeautifulSoup(html_code, features="html.parser")
        items_tag = soup.select("#mf-shop-content > .products > li")
        for item_tag in items_tag:
            product_details = self._parse_product(item_tag)
            self.parsed_products += 1

            # don't update the product details in DB if price didn't change
            sku = product_details.get("sku")
            price = product_details.get("price")
            if cache and cache.get(sku) == price: continue

            # download image and get product object
            # ignore product if failed to download image of the product
            product = self._to_product(product_details)
            if not product: continue

            # save product price in cache
            if cache: cache.set(product.sku, product.price)
            self.products[sku] = product
            self.scraped_with_image += 1

    def save(self, storage: Storage) -> None:
        logging.info("Saving products in DB.")
        self.updated_in_db = 0
        for product in self.products.values():
            storage.put(product.sku, product.asdict)
            self.updated_in_db += 1
        storage.commit()

    def notify(self) -> None:
        logging.info(f"Parsed {self.parsed_products} products from {config.N_PAGES} pages.")
        logging.info(f"Downloaded {self.scraped_with_image} images of products.")
        logging.info(f"Updated {self.updated_in_db} products in database.")
