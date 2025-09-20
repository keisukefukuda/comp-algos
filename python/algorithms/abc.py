from abc import ABC, abstractmethod


class Compresssor(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> str:
        pass

    @abstractmethod
    def decode(self, encoded: str) -> bytes:
        pass
