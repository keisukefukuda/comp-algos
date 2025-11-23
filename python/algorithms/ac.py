import math
from fractions import Fraction
from typing import Any

import tqdm  # noqa

from algorithms.abc import Compresssor, AlphabetType, PMFType, CDFType


def find_range_minimum_bits(L: Fraction, U: Fraction) -> str:
    k = math.ceil(-math.log2(U - L))
    while True:
        n = math.ceil(L * (1 << k))
        if n + 1 < (U * (1 << k)):
            bits = format(int(n), "b").zfill(k)
            return bits
        else:
            k += 1


def find_range_index(
    CDF: list[Fraction] | list[float], L: Fraction, U: Fraction
) -> int | None:
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


class AC(Compresssor):
    def __init__(self) -> None:
        pass

    def encode(self, data: bytes) -> dict:
        assert type(data) is bytes
        ret: dict[str, Any] = {}

        A = sorted(list(set(data)))
        F: PMFType = [data.count(a) for a in A]
        M = sum(F)
        Index = {a: i for i, a in enumerate(A)}
        C: CDFType = [sum(F[: i + 1], 0) for i in range(len(A))]
        C_f = [Fraction(v, M) for v in C]

        print("Alphabet:", A)
        print("Total Frequency (M):", M)
        print("Index Mapping:", Index)
        print("PMF:", [float(v) / M for v in F])
        print("CDF:", [float(v) / M for v in C])

        meta = {
            "A": A,
            "F": F,
            "C": C,
            "C_f": C_f,
            "M": M,
        }

        if len(A) == 0:
            return {"data": "", "meta": {}}

        data_out = ""  # List to store the in_data bits

        # print(f"{data=}")

        for s in tqdm.tqdm(data, desc="Encoding"):
            i = Index[s]
            L = Fraction(0, 1) if i == 0 else Fraction(C[i - 1], M)
            U = Fraction(C[i], M)
            bits = find_range_minimum_bits(L, U)
            # print(f"Symbol: {s}, Interval: [{L}, {U}), Encoded bits: {bits}")
            data_out += bits

        # print("Encoded data:", in_data)
        ret["data"] = data_out
        ret["meta"] = meta

        return ret

    def decode(self, encoded: dict[str, Any]) -> bytes | bytearray:
        decoded = bytearray()
        i = 0

        in_data = encoded["data"]
        meta = encoded["meta"]  # noqa

        if len(in_data) == 0:
            return bytes()

        A: AlphabetType = meta["A"]
        # F: PMFType = meta["F"]
        # C: CDFType = meta["C"]
        C_f: list[Fraction] = meta["C_f"]
        # M: int = meta["M"]

        if in_data == "":
            return bytearray()

        pbar: tqdm.tqdm = tqdm.tqdm(total=len(in_data), desc="Decoding")

        nbits = 0
        L = Fraction(0, 1)
        U = Fraction(1, 1)
        while i < len(in_data):
            s = in_data[i]
            nbits += 1
            L = L + Fraction(1, 2**nbits) if s == "1" else L
            U = L + Fraction(1, 2**nbits)
            # print(f"Looking for range: {i=} read bits = {nbits}, {s=} {L=}, {U=}")  # noqa

            if (j := find_range_index(C_f, L, U)) is not None:
                decoded.append(A[j])
                # print(f"Bits = {in_data[i-nbits+1:i+1]}")
                # print(f"Decoded symbol: {A[j]}, Interval: [{L}, {U}), Bits used: {nbits}")  # noqa
                # print("")
                nbits = 0
                L = Fraction(0, 1)
                U = Fraction(1, 1)

            pbar.update(1)
            i += 1
        if nbits != 0:
            assert False, (
                "Decoding failed: remaining bits:",
                f"{in_data[i - nbits : i]}",
            )

        return bytes(decoded)
