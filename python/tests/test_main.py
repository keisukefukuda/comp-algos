import pytest  # noqa

from algorithms.abc import Compresssor  # noqa
from algorithms.ac import AC  # noqa
from algorithms.rans import RANS, RANSEncoded  # noqa


_comp_algos = [
    AC,
    RANS,
]
_data = [
    b"",
    b"hello, rans! hello, rans! hello, rans!",
    b"a",
    b"a" * 1000,
    b"abcde" * 1000,
]


# @pytest.mark.parametrize("algorithm_class,data", [_comp_algos, _data])
@pytest.mark.parametrize("algorithm_class", _comp_algos)
@pytest.mark.parametrize("data", _data)
def test_main(algorithm_class: type[Compresssor], data: bytes):
    assert type(data) is bytes
    encoded = algorithm_class().encode(data)

    if algorithm_class is RANS:
        assert type(encoded) is RANSEncoded
        assert type(encoded.data) is str, "data is str"
        assert encoded.meta is not None, "has 'meta'"
    else:
        assert type(encoded) is dict
        assert "data" in encoded, "has 'data' key"
        assert type(encoded["data"]) is str, "data is str"
        assert "meta" in encoded, "has 'meta' key"

    decoded: bytes = algorithm_class().decode(encoded)
    assert type(decoded) is bytearray or type(decoded) is bytes
    assert data == decoded


def test_encode_with_external_freq_table():
    """正しい freq_table を渡した場合にラウンドトリップが成功する"""
    data = b"abcde" * 100
    rans = RANS()
    A, F, _ = rans.build_frequency_table(data, M=4096)
    encoded = rans.encode(data, freq_table=(A, F))
    assert type(encoded) is RANSEncoded
    decoded = rans.decode(encoded)
    assert decoded == data


def test_encode_with_inaccurate_freq_table():
    """実際の分布と異なる頻度テーブルでもエンコード・デコードが成功する"""
    data = b"abcde" * 100
    rans = RANS()
    # a〜e が均一分布のデータに対して、意図的に偏った頻度を指定
    A = sorted(set(data))   # [97, 98, 99, 100, 101]
    F = [4090, 1, 1, 1, 3]  # 実際の分布と異なる頻度
    encoded = rans.encode(data, freq_table=(A, F))
    assert type(encoded) is RANSEncoded
    decoded = rans.decode(encoded)
    assert decoded == data


def test_encode_with_freq_table_missing_symbol():
    """data に含まれるシンボルが freq_table の A にない場合 AssertionError"""
    data = b"abcz"
    rans = RANS()
    A = [97, 98, 99]        # z (122) が含まれない
    F = [1000, 1000, 2096]
    with pytest.raises(AssertionError):
        rans.encode(data, freq_table=(A, F))


def test_encode_with_freq_table_length_mismatch():
    """A と F の長さが不一致の場合 AssertionError"""
    data = b"abc"
    rans = RANS()
    A = [97, 98, 99]   # 長さ3
    F = [2000, 2096]   # 長さ2 (不一致)
    with pytest.raises(AssertionError):
        rans.encode(data, freq_table=(A, F))
