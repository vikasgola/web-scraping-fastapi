import requests, os

from bs4 import BeautifulSoup, Tag
from src.product import Product
from src.storage import Storage

IMAGES_PATH = "resources/images/"


class DentalStall:
    DENTAL_STALL_URL: str = "https://dentalstall.com/shop/page/{}/"
    DENTAL_STALL_HEADERS: dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }

    def __init__(self) -> None:
        self.products: dict[str, Product] = {}
        self.updated_in_db: int = 0
        self.scraped_with_image: int = 0

    def parse_page(self, nth_page: int):
        html_code = self.fetch_page(nth_page)
        self._parse_page_html(html_code)

    def fetch_page(self, page_number: int) -> str:
        # with open("resources/page_1.html") as page_1:
        #     return page_1.read()
        response = requests.get(
            self.DENTAL_STALL_URL.format(page_number),
            headers=self.DENTAL_STALL_HEADERS
        )
        return response.text

    def _to_product(self, product_details: dict[str, str]) -> str:
        image_url = product_details.pop("image_url")
        file_name = product_details.get("sku") + "." + image_url.split(".")[-1]
        response = requests.get(image_url)
        if response.status_code == 200:
            file_path = IMAGES_PATH + file_name
            if not os.path.exists(IMAGES_PATH):
                os.makedirs(IMAGES_PATH)
            with open(file_path, "wb") as f:
                f.write(response.content)
            product_details["image_path"] = file_path
            return Product(**product_details)
        else:
            print(f"failed to download image for {product_details.get('sku')} from image_url.")
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

        item_title = item_title_tag and item_title_tag.text.strip()
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
            # check if price hasn't changed using caching
            # if yes, then download

            product = self._to_product(product_details)
            if not product: continue

            self.products[product.sku] = product
            self.scraped_with_image += 1

    def save(self, storage: Storage):
        self.updated_in_db = 0
        for product in self.products.values():
            storage.put(product.sku, product.asdict)
            self.updated_in_db += 1
        storage.commit()
