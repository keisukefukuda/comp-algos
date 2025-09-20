from abc import ABC, abstractmethod
from typing import TypeAlias


# Type alias for Probability Mass Function table
PMFType: TypeAlias = list[int]
CDFType: TypeAlias = list[int]


class Compresssor(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> str:
        pass

    @abstractmethod
    def decode(self, encoded: str) -> bytes:
        pass

    @property
    @abstractmethod
    def A(self) -> list[int]:
        pass
