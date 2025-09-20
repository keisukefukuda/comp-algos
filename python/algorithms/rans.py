import math
from fractions import Fraction
from typing import TypeAlias

import tqdm  # noqa

from algorithms.abc import Compresssor


# Type alias for Probability Mass Function table
PMFType: TypeAlias = list[Fraction]
CDFType: TypeAlias = list[Fraction]


def ch(x: int) -> str:
    if 32 <= x < 127:
        return chr(x)
    elif x == ord("\n"):
        return "\\n"
    return "<?>"


def pr(x: int) -> str:
    B = 10000000
    if x < 10000000:
        return str(x)
    else:
        x2 = x
        while x2 > B:
            x2 //= B
        return f"{x2}...{x % B:07d}"


class RANS(Compresssor):  # rANS
    def __init__(self):
        pass

    def encode(self, data: bytes) -> str:
        assert type(data) is bytes
        if len(data) == 0:
            return ""

        self.A: list[int] = sorted(list(set(data)))
        self.F: list[int] = [data.count(a) for a in self.A]
        self.M: int = sum(self.F)
        # Index = {a: i for i, a in enumerate(self.A)}
        self.C: list[int] = [sum(self.F[: i + 1]) for i in range(len(self.A))]

        print("Alphabet:", self.A)
        print("Total Frequency (M):", self.M)
        print("PMF:", [float(v) for v in self.F])
        print("CDF:", [float(v) for v in self.C])

        if len(self.A) == 0:
            return ""

        x: int = 0  # Initial state

        idx = self.A.index(data[0])

        for s in tqdm.tqdm(data, desc="Encoding"):
            x_prev = x
            idx = self.A.index(s)
            Fs = self.F[idx]
            Cs = self.C[idx - 1] if idx > 0 else 0
            block_id = (x // Fs) * self.M
            slot = Cs + x % Fs
            # print(
            #     f"Push {s} {ch(s)}: block_id={pr(block_id)} {slot=} {idx=} {Fs=} {Cs=}"
            # )  # noqa

            x = block_id + slot
            # print(f"   x: {pr(x_prev)} -> {pr(x)}")

        return f"{len(data)}_" + str(x)

    def decode(self, encoded: str) -> bytes:
        decoded = bytearray()

        l_str, x_str = encoded.split("_")
        length: int = int(l_str)

        if length == 0:
            return decoded

        x = int(x_str)

        for _ in tqdm.tqdm(range(length), desc="Decoding"):
            # print(f"Decoding step: x={pr(x)}")
            x_prev = x  # noqa
            slot = x % self.M

            # s = C_inv(slot)
            for i in range(len(self.C)):
                L = self.C[i - 1] if i > 0 else 0
                U = self.C[i]
                # print(
                #     f"  {i=}, {slot=}, {L=}, {U=} c={self.C[i]} s={self.A[i]} {ch(self.A[i])}"
                # )
                if L <= slot < U:
                    s = self.A[i]
                    # print(
                    #     f"     ==> Found slot for symbol! index {i}: {s=} {ch(s)} [{L}, {self.C[i]})"
                    # )  # noqa
                    decoded.append(s)
                    Cs = L
                    break
            x = self.F[i] * (x // self.M) + slot - Cs
            # print(f"   x: {pr(x_prev)} -> {pr(x)}")

        return bytes(decoded[::-1])  # Reverse the decoded data
