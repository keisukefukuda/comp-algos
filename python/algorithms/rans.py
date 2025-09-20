import tqdm  # noqa

from algorithms.abc import Compresssor, PMFType, CDFType


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
    _A: list[int]  # Alphabet
    _F: PMFType  # Frequency table
    _C: CDFType  # Cumulative frequency table
    _M: int  # Total frequency
    B: int  # Renormalization Base
    k: int  # Renormalization granularity (bits)

    def __init__(self) -> None:
        self.B: int = 2**12  # Renormalization Base
        self.k: int = 8  # Renormalization granularity (bits)

    @property
    def A(self) -> list[int]:
        return self._A

    @property
    def PMF(self) -> PMFType:
        return self._F

    @property
    def CDF(self) -> CDFType:
        return self._C

    @property
    def M(self) -> int:
        return self._M

    def encode(self, data: bytes) -> str:
        assert type(data) is bytes
        if len(data) == 0:
            return ""

        self._A = sorted(list(set(data)))
        self._F = [data.count(a) for a in self.A]
        self._M: int = sum(self._F, 0)
        # Index = {a: i for i, a in enumerate(self.A)}
        self._C: CDFType = [sum(self._F[: i + 1]) for i in range(len(self.A))]

        print("Alphabet:", self.A)
        print("Total Frequency (M):", self.M)
        print("PMF:", [float(v) / self.M for v in self.PMF])
        print("CDF:", [float(v) / self.M for v in self.CDF])

        if len(self.A) == 0:
            return ""

        x: int = 0  # Initial state

        idx = self.A.index(data[0])

        encoded = ""

        for s in tqdm.tqdm(data, desc="Encoding"):
            x_prev = x  # noqa
            idx = self.A.index(s)
            Fs = self._F[idx]
            Cs = self._C[idx - 1] if idx > 0 else 0
            block_id = (x // Fs) * self.M
            slot = Cs + x % Fs
            print(
                f"Push {s} {ch(s)}: block_id={pr(block_id)} {slot=} {idx=} {Fs=} {Cs=}"
            )  # noqa

            x = block_id + slot
            # renormalization
            while x >= self.B:
                bits = x & ((1 << self.k) - 1)
                bits_str = format(bits, "b").zfill(self.k)
                encoded += bits_str
                x >>= self.k
                print(f"  Renormalize: emit {bits_str=}, new x={pr(x)}")
            print(f"   x: {pr(x_prev)} -> {pr(x)}")
        print(f"Final state x={pr(x)}")
        encoded = "_".join([str(len(data)), str(x), encoded])
        print(f"Encoded : {encoded}")
        return encoded

    def decode(self, encoded: str) -> bytes:
        decoded = bytearray()

        l_str, x_str, body_str = encoded.split("_")
        length: int = int(l_str)
        x = int(x_str)

        if length == 0:
            return decoded

        assert len(body_str) % self.k == 0

        for _ in tqdm.tqdm(range(length), desc="Decoding"):
            x_prev = x  # noqa
            print(f"Decoding step: x={pr(x)}")
            slot = x % self.M

            # s = C_inv(slot)
            for i in range(len(self.CDF)):
                L = self.CDF[i - 1] if i > 0 else 0
                U = self.CDF[i]
                print(
                    f"  {i=}, {slot=}, {L=}, {U=} c={self.CDF[i]} s={self.A[i]} {ch(self.A[i])}"
                )
                if L <= slot < U:
                    s = self.A[i]
                    print(
                        f"     ==> Found slot for symbol! index {i}: {s=} {ch(s)} [{L}, {self.CDF[i]})"
                    )  # noqa
                    decoded.append(s)
                    Cs = L
                    break
            x = self.PMF[i] * (x // self.M) + slot - Cs
            print(f"   x: {pr(x_prev)} -> {pr(x)}")

            while len(body_str) >= self.k and x < self.B:
                bits_str = body_str[-self.k :]
                bits = int(bits_str, 2)
                body_str = body_str[: -self.k]
                x = (x << self.k) | bits
                print(f"  Renormalize: read {bits_str} = {bits}, new x={pr(x)}")

        return bytes(decoded[::-1])  # Reverse the decoded data
