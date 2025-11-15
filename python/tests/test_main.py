from typing import Any

import pytest  # noqa

from algorithms.abc import Compresssor
from algorithms.ac import AC1
from algorithms.rans import RANS


@pytest.mark.parametrize("algorithm_classes", [[AC1, RANS]])
def test_main(algorithm_classes: type[Compresssor]):
    data = b"hello, rans! hello, rans! hello, rans!"
    for algo_cls in algorithm_classes:
        assert type(data) is bytes
        comp: Compresssor = algo_cls()
        encoded: dict[str, Any] = comp.encode(data)

        assert type(encoded) is dict
        assert "data" in encoded, "has 'data' key"
        assert "meta" in encoded, "has 'meta' key"
        decoded: bytes = comp.decode(encoded)
        assert data == decoded
