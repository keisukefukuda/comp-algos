from abc import ABC, abstractmethod
from typing import Any, TypeAlias


# Type alias for Probability Mass Function table
PMFType: TypeAlias = list[int]
CDFType: TypeAlias = list[int]
AlphabetType: TypeAlias = list[int]


class Compresssor(ABC):
    @abstractmethod
    def encode(self, data: bytes) -> Any:
        pass

    @abstractmethod
    def decode(self, encoded: Any) -> bytes:
        pass
