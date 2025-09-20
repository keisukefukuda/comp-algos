import math
from fractions import Fraction

import tqdm  # noqa

from algorithms.abc import Compresssor, PMFType, CDFType


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


class AC1(Compresssor):
    _pmf: PMFType  # Probability Mass Function table
    _cdf: CDFType  # Cumulative Distribution Function table
    _A: list[int]  # Alphabet
    _M: int  # Total frequency

    @property
    def A(self) -> list[int]:
        return self._A

    @property
    def PMF(self) -> PMFType:
        return self._pmf

    @property
    def CDF(self) -> CDFType:
        return self._cdf

    @property
    def M(self) -> int:
        return self._M

    def encode(self, data: bytes) -> str:
        assert type(data) is bytes
        self._A = sorted(list(set(data)))
        self._pmf: PMFType = [data.count(a) for a in self._A]
        self._M = sum(self._pmf)
        Index = {a: i for i, a in enumerate(self._A)}
        self._cdf: CDFType = [sum(self._pmf[: i + 1], 0) for i in range(len(self._A))]
        self._cdf_f = [Fraction(v, self.M) for v in self._cdf]

        if len(self.A) == 0:
            return ""

        print("Alphabet:", self.A)
        print("Total Frequency (M):", self.M)
        print("Index Mapping:", Index)
        print("PMF:", [float(v) / self.M for v in self.PMF])
        print("CDF:", [float(v) / self.M for v in self.CDF])

        encoded = ""  # List to store the encoded bits

        # print(f"{data=}")

        for s in tqdm.tqdm(data, desc="Encoding"):
            i = Index[s]
            L = Fraction(0, 1) if i == 0 else Fraction(self.CDF[i - 1], self.M)
            U = Fraction(self.CDF[i], self.M)
            bits = find_range_minimum_bits(L, U)
            # print(f"Symbol: {s}, Interval: [{L}, {U}), Encoded bits: {bits}")
            encoded += bits

        # print("Encoded data:", encoded)
        return encoded

    def decode(self, encoded: str) -> bytes:
        decoded = bytearray()
        i = 0

        if encoded == "":
            return bytearray()

        pbar: tqdm.tqdm = tqdm.tqdm(total=len(encoded), desc="Decoding")

        nbits = 0
        L = Fraction(0, 1)
        U = Fraction(1, 1)
        while i < len(encoded):
            s = encoded[i]
            nbits += 1
            L = L + Fraction(1, 2**nbits) if s == "1" else L
            U = L + Fraction(1, 2**nbits)
            # print(f"Looking for range: {i=} read bits = {nbits}, {s=} {L=}, {U=}")  # noqa

            if (j := find_range_index(self._cdf_f, L, U)) is not None:
                decoded.append(self.A[j])
                # print(f"Bits = {encoded[i-nbits+1:i+1]}")
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
                f"{encoded[i - nbits : i]}",
            )

        return bytes(decoded)


def ac_1(data: bytes):
    # Very simple arithmetic coding
    # with static probability model (i.e. per-symbol frequencies)
    ac = AC1()

    encoded = ac.encode(data)
    decoded = ac.decode(encoded)

    print("\nDecoding process:")

    if data == decoded:
        print("Data successfully encoded and decoded!")
        print("Alphabet size:", len(ac.A))
        print("Data length: ", len(data), "symbols")
        print(f"Encoded length: {len(encoded)} bits = {len(encoded) / 8:.2f} bytes")  # noqa
        if len(data) > 0:
            orig_bites = len(data) * 8
            enc_bits = len(encoded)
            print(f"Compression rate: {orig_bites / enc_bits:.2f}x")
    else:
        raise RuntimeError("Decoded data does not match original!")
