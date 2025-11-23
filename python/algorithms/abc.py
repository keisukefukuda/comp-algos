from abc import ABC, abstractmethod
from typing import TypeAlias


# Type alias for Probability Mass Function table
PMFType: TypeAlias = list[int]
CDFType: TypeAlias = list[int]
AlphabetType: TypeAlias = list[int]


class Compresssor(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> dict:
        pass

    @abstractmethod
    def decode(self, encoded: dict) -> bytes:
        pass
