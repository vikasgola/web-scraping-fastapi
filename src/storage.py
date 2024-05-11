import json
import os
import typing

from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def put(self, key: str, value: dict[str, dict]):
        pass

    @abstractmethod
    def commit(self):
        pass


class JsonFileStorage(Storage):
    def __init__(self, path) -> None:
        super().__init__()
        self.path = path
        self.is_loaded = False

    def _load(self) -> None:
        try:
            directory = os.path.dirname(self.path)
            os.makedirs(directory, exist_ok=True)
            with open(self.path, "r") as f:
                self.data = json.load(f)
        except FileNotFoundError as err:
            self.data = {}
        self.is_loaded = True

    def get(self, key: str) -> typing.Any:
        if not self.is_loaded: self._load()
        return self.data.get(key)

    def put(self, key: str, value: dict[str, dict]) -> None:
        if not self.is_loaded: self._load()
        self.data[key] = value

    def commit(self) -> None:
        if not self.is_loaded: return
        with open(self.path, "w") as f:
            json.dump(self.data, f, indent=4)
