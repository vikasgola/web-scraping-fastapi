import json

from abc import ABC, abstractmethod

class Storage(ABC):
    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def put(self, key: str, value: dict[str, dict]):
        pass


class JsonFileStorage(Storage):
    def __init__(self, path) -> None:
        super().__init__()

        self.path = path
        try:
            with open(path, "r") as f:
                self.data = json.load(f)
        except FileNotFoundError as err:
            self.data = {}

    def get(self, key: str):
        return self.data.get(key)

    def put(self, key: str, value: dict[str, dict]):
        self.data[key] = value
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)
