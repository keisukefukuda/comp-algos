from typing import Any

import pytest  # noqa

from algorithms.abc import Compresssor
from algorithms.ac import AC1
from algorithms.rans import RANS


_comp_algos = [
    AC1,
    RANS,
]
_data = [
    b"",
    b"hello, rans! hello, rans! hello, rans!",
    b"",
    b"a",
    b"a" * 1000,
    b"abcde" * 500,
]


# @pytest.mark.parametrize("algorithm_class,data", [_comp_algos, _data])
@pytest.mark.parametrize("algorithm_class", _comp_algos)
@pytest.mark.parametrize("data", _data)
def test_main(algorithm_class: type[Compresssor], data: bytes):
    assert type(data) is bytes
    encoded: dict[str, Any] = algorithm_class().encode(data)

    assert type(encoded) is dict
    assert "data" in encoded, "has 'data' key"
    assert type(encoded["data"]) is str, "data is str"
    assert "meta" in encoded, "has 'meta' key"

    decoded: bytes = algorithm_class().decode(encoded)
    assert type(decoded) is bytearray or type(decoded) is bytes
    assert data == decoded
