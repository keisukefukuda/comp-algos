import math
from fractions import Fraction
from typing import TypeAlias

import fire  # noqa
import tqdm  # noqa


# Type alias for Probability Mass Function table
PMFType: TypeAlias = list[Fraction]
CDFType: TypeAlias = list[Fraction]


def find_range_minimum_bits(L: Fraction, U: Fraction) -> str:
    k = math.ceil(-math.log2(U - L))
    while True:
        n = math.ceil(L * (1 << k))
        if n + 1 < (U * (1 << k)):
            bits = format(int(n), 'b').zfill(k)
            return bits
        else:
            k += 1


def find_range_index(CDF: CDFType, L: Fraction, U: Fraction) -> int | None:
    # Find L:
    for j in range(len(CDF)):
        range_L = CDF[j - 1] if j > 0 else Fraction(0, 1)
        range_U = CDF[j]
        # print(f"  {j=}, {L=}, {U=}, {range_L=}, {range_U=}")
        if range_L <= L and U < range_U:
            # Found the range and symbol
            # print(f"     ==> Found range for symbol! index {j}: [{range_L}, {range_U})")  # noqa
            return j
    return None


class AC1(object):
    def encode(self, data: bytes) -> tuple[str, list[int], list[int], CDFType]:
        assert type(data) is bytes
        A: list[int] = sorted(list(set(data)))
        freq = [data.count(a) for a in A]
        M = sum(freq)
        Index = {a: i for i, a in enumerate(A)}
        PMF = [Fraction(f, M) for f in freq]
        CDF: CDFType = [Fraction(sum(PMF[:i + 1])) for i in range(len(A))]

        if len(A) == 0:
            return "", A, freq, CDF

        print("Alphabet:", A)
        print("Total Frequency (M):", M)
        print("Index Mapping:", Index)
        print("PMF:", [float(v) for v in PMF])
        print("CDF:", [float(v) for v in CDF])

        encoded = ""  # List to store the encoded bits

        # print(f"{data=}")

        for s in tqdm.tqdm(data, desc="Encoding"):
            i = Index[s]
            L = Fraction(0, 1) if i == 0 else CDF[i - 1]
            U = CDF[i]
            bits = find_range_minimum_bits(L, U)
            # print(f"Symbol: {s}, Interval: [{L}, {U}), Encoded bits: {bits}")
            encoded += bits

        # print("Encoded data:", encoded)
        return encoded, A, freq, CDF

    def decode(self, encoded: str, A, freq, CDF) -> bytearray:
        decoded = bytearray()
        i = 0

        if encoded == "":
            return bytearray()

        pbar = tqdm.tqdm(total=len(encoded), desc="Decoding")

        nbits = 0
        L = Fraction(0, 1)
        U = Fraction(1, 1)
        while i < len(encoded):
            s = encoded[i]
            nbits += 1
            L = L + Fraction(1, 2**nbits) if s == '1' else L
            U = L + Fraction(1, 2**nbits)
            # print(f"Looking for range: {i=} read bits = {nbits}, {s=} {L=}, {U=}")  # noqa

            if (j := find_range_index(CDF, L, U)) is not None:
                decoded.append(A[j])
                # print(f"Bits = {encoded[i-nbits+1:i+1]}")
                # print(f"Decoded symbol: {A[j]}, Interval: [{L}, {U}), Bits used: {nbits}")  # noqa
                # print("")
                nbits = 0
                L = Fraction(0, 1)
                U = Fraction(1, 1)

            pbar.update(1)
            i += 1
        if nbits != 0:
            assert False, ("Decoding failed: remaining bits:",
                           f"{encoded[i-nbits:i]}")

        return decoded


def ac_1(data: bytes):
    # Very simple arithmetic coding 
    # with static probability model (i.e. per-symbol frequencies)
    ac = AC1()

    encoded, A, freq, CDF = ac.encode(data)
    decoded = ac.decode(encoded, A, freq, CDF)

    print("\nDecoding process:")

    if data == decoded:
        print("Data successfully encoded and decoded!")
        print("Alphabet size:", len(A))
        print("Data length: ", len(data), "symbols")
        print(f"Encoded length: {len(encoded)} bits = {len(encoded)/8:.2f} bytes")  # noqa
        if len(data) > 0:
            orig_bites = len(data) * 8
            enc_bits = len(encoded)
            print(f"Compression rate: {orig_bites/enc_bits:.2f}x")
    else:
        raise RuntimeError("Decoded data does not match original!")


def main(in_file: str):
    with open(in_file, 'rb') as f:
        data = f.read()
    ac_1(data)


if __name__ == "__main__":
    fire.Fire(main)
