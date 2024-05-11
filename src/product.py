from dataclasses import dataclass, asdict

@dataclass
class Product:
    sku: str
    title: str
    price: str
    image_path: str

    @property
    def asdict(self):
        return asdict(self)
