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
    b"hello, rans! hello, rans! hello, rans!",
    b"",
]


# @pytest.mark.parametrize("algorithm_class,data", [_comp_algos, _data])
@pytest.mark.parametrize("algorithm_class", _comp_algos)
@pytest.mark.parametrize("data", _data)
def test_main(algorithm_class: type[Compresssor], data: bytes):
    assert type(data) is bytes
    comp: Compresssor = algorithm_class()
    encoded: dict[str, Any] = comp.encode(data)

    assert type(encoded) is dict
    assert "data" in encoded, "has 'data' key"
    assert "meta" in encoded, "has 'meta' key"
    decoded: bytes = comp.decode(encoded)
    assert data == decoded
