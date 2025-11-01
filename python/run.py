import fire  # noqa

from algorithms.abc import Compresssor
from algorithms.ac import AC1
from algorithms.rans import RANS

Algorithms = {"ac1": AC1, "rans": RANS}


def main(algo: str, in_file: str):
    with open(in_file, "rb") as f:
        data = f.read()

    if algo not in Algorithms:
        raise ValueError(f"Unknown algorithm: {algo}")

    algo_cls = Algorithms.get(algo)
    assert algo_cls is not None

    comp: Compresssor = algo_cls()

    encoded: str = comp.encode(data)
    decoded: bytes = comp.decode(encoded)

    print("\nDecoding process:")

    if data == decoded:
        print("Data successfully encoded and decoded!")
        print("Alphabet size:", len(comp.A))
        print("Data length: ", len(data), "symbols")
        print(f"Encoded length: {len(encoded)} bits = {len(encoded) / 8:.2f} bytes")  # noqa
        if len(data) > 0:
            orig_bites = len(data) * 8
            enc_bits = len(encoded)
            print(f"Compression rate: {orig_bites / enc_bits:.2f}x")
    else:
        print("Error: decoded data does not match original!")
        print(f"Original data: {len(data)} {data[:20]!r}...")
        print(f"Decoded data:  {len(decoded)} {decoded[:20]!r}...")
        raise RuntimeError(
            f"Decoded data does not match original! {data!r} != {decoded!r}"
        )


if __name__ == "__main__":
    fire.Fire(main)
