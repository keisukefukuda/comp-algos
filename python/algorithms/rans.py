import tqdm  # noqa

from algorithms.abc import Compresssor, PMFType, CDFType


def ch(x: int) -> str:
    if 32 <= x < 127:
        return chr(x)
    elif x == ord("\n"):
        return "\\n"
    return "<?>"


def pr(x: int) -> str:
    B = 2**32
    if x < B:
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
    do_norm: bool

    def __init__(self) -> None:
        self.k: int = 4  # Renormalization granularity (bits)
        self.L: int = 2**4  # Upper bound of the state X
        self.b: int = 1 << self.k  # emit base (emit b bits in each renorm)
        self.bL: int = self.b * self.L
        self.do_norm = True
        assert self.L >= self.b

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
        # self._C: CDFType = [sum(self._F[: i]) for i in range(len(self.A))]
        self._C: CDFType = []
        cum = 0
        for f in self._F:
            self._C.append(cum)
            cum += f
        # self._C: CDFType = [sum(self._F[: i+1]) for i in range(len(self.A))]

        print("Alphabet:", self.A)
        print("Total Frequency M=", self.M)
        print("PMF:", [v for v in self.PMF])
        print("PMF / M:", [float(v) / self.M for v in self.PMF])
        print("CDF:", [v for v in self.CDF])
        print("CDF / M:", [float(v) / self.M for v in self.CDF])
        print(f"Renormalization base k={self.k}, b={self.b}, L={self.L}, bL={self.bL}")

        if len(self.A) == 0:
            return ""

        x: int = self.L  # Initial state

        idx = self.A.index(data[0])

        encoded = ""

        for step, s in tqdm.tqdm(enumerate(data), desc="Encoding"):
            print("\nEncoding step:", step)
            idx = self.A.index(s)
            Fs = self._F[idx]
            Cs = self._C[idx]

            # renormalization
            if self.do_norm:
                while x >= Fs * self.L:
                    x_prev = x
                    bits = x & (self.b - 1)
                    bits_str = format(bits, "b").zfill(self.k)
                    encoded += bits_str
                    x >>= self.k
                    print(
                        f"  Renormalize: (∵ x={x_prev} >= {Fs * self.L=}）: emit {bits} str={bits_str}, new x={pr(x)}"
                    )

            assert 0 <= x <= self.M * self.L - 1

            # assert self.L <= x < self.bL, f"Invalid state: L={self.L} <= x < {self.bL}, but x={x}, {x_prev=}"  # noqa

            x_prev = x  # noqa
            idx = self.A.index(s)
            block_id = x // Fs
            slot = Cs + (x % Fs)
            print(
                f"  Push {s} {ch(s)}: block_id={pr(block_id)} {slot=} {idx=} {Fs=} {Cs=}"
            )  # noqa
            x = block_id * self.M + slot
            print(f"   x : {pr(x_prev)} -> {pr(x)}  PUSH {ch(s)}")
            print(
                f"   x = {x}  : x = {block_id * self.M=} + {slot=} = {block_id * self.M + slot}"
            )

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

        print("Decoding: initial state x=", pr(x))

        for step in tqdm.tqdm(range(length), desc="Decoding"):
            print("\nDecoding step:", step)
            x_prev = x  # noqa
            r, q = divmod(x, self.M)
            slot = q
            # slot = x % self.M  # initial slot value
            print(f"  X={pr(x)} {slot=}")

            # s = C_inv(slot)
            pop_i, Cs, Fs = self.pop_s(slot)
            s = self.A[pop_i]
            decoded.append(s)
            # x = (x // self.M) * Fs + slot - Cs
            x = r * Fs + slot - Cs
            print(f"  x : {pr(x_prev)} -> {pr(x)} POP {ch(s)}")

            # renormalization
            if self.do_norm:
                while x < min(self.L, self.M):
                    print(f"  Renormalize: {x=} < L={self.L}")
                    bits_str = body_str[-self.k :]
                    bits = int(bits_str, 2)
                    body_str = body_str[: -self.k]
                    x = (x << self.k) | bits
                    print(f"  Renormalize: read {bits_str} = {bits}, new x={pr(x)}")

        return bytes(decoded[::-1])  # Reverse the decoded data

    def pop_s(self, slot) -> tuple[int, int, int]:
        for i in range(len(self._F)):
            Cs = self._C[i]
            Fs = self._F[i]
            # U = self.CDF[i + 1] if i + 1 < len(self.CDF) else self.M
            # print(
            #     f"  {i=}, {Cs=}, {Fs=} c={self.CDF[i]} s={self.A[i]} {ch(self.A[i])}"
            # )
            if Cs <= slot < Cs + Fs:
                s = self.A[i]
                print(
                    f"  ==> Found slot for symbol! index {i}: {s=} '{ch(s)}' {Cs=} {Fs=} [{Cs}, {Cs + Fs})"
                )  # noqa
                return i, Cs, Fs
        raise RuntimeError(f"Decoding failed: slot {slot} not found in CDF")
