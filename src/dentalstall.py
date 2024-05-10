import requests

from bs4 import BeautifulSoup, Tag
from src.product import Product
from src.storage import Storage


class DentalStall:
    DENTAL_STALL_URL: str = "https://dentalstall.com/shop/page/{}/"
    DENTAL_STALL_HEADERS: dict[str, str] = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_2) AppleWebKit/601.3.9 (KHTML, like Gecko) Version/9.0.2 Safari/601.3.9'
    }

    def __init__(self) -> None:
        self.products: dict[str, Product] = {}

    def parse_page(self, nth_page: int):
        print("started scraping!", nth_page)
        html_code = self.fetch_page(nth_page)
        self._parse_page_html(html_code)
        print("done!", nth_page)

    def fetch_page(self, page_number: int) -> str:
        # with open("resources/page_1.html") as page_1:
        #     return page_1.read()
        response = requests.get(
            self.DENTAL_STALL_URL.format(page_number),
            headers=self.DENTAL_STALL_HEADERS
        )
        return response.text

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
        item_src = thumbnail_tag and thumbnail_tag.get("href")
        item_sku = item_other_tag and item_other_tag.get("data-product_sku").strip()
        return Product(
            sku=item_sku, title=item_title, price=item_price,
            image_url=item_image_src, url=item_src
        )

    def _parse_page_html(self, html_code: str) -> None:
        soup = BeautifulSoup(html_code, features="html.parser")
        items_tag = soup.select("#mf-shop-content > .products > li")
        for item_tag in items_tag:
            product = self._parse_product(item_tag)
            self.products[product.sku] = product
            print(f"added {product.sku}")

    def save(self, storage: Storage):
        for product in self.products.values():
            stored_product = storage.get(product.sku)
            if stored_product and stored_product.get("price") == product.price:
                return
            storage.put(product.sku, product.asdict)
