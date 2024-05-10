from dataclasses import dataclass, asdict

@dataclass
class Product:
    sku: str
    title: str
    price: str
    image_url: str
    url: str

    @property
    def asdict(self):
        return asdict(self)

