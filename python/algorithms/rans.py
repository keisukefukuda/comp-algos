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


def argmax(lst: list[int]) -> int:
    max_i = 0
    max_v = lst[0]
    for i, v in enumerate(lst):
        if v > max_v:
            max_v = v
            max_i = i
    return max_i


class RANS(Compresssor):  # rANS
    A: list[int]  # Alphabet
    F: PMFType  # Frequency table
    C: CDFType  # Cumulative frequency table
    M: int  # Total frequency
    k: int  # Renormalization granularity (bits)

    def __init__(self) -> None:
        self.k: int = 8  # renormalization granularity (bits)
        self.b: int = 256  # emit base (emit b bits in each renorm)
        self.L: int = 2**23  # = 8,388,608 Lower bound of the state X
        self.bL: int = self.b * self.L
        self.M = 4096  # 2^12
        assert self.L > self.M and self.L % self.M == 0
        assert self.L >= self.b and self.L % self.b == 0

    def encode(self, data: bytes) -> str:
        assert type(data) is bytes
        if len(data) == 0:
            return ""

        self.A = sorted(list(set(data)))
        assert len(self.A) <= self.M, (
            f"Alphabet size too large: |A|={len(self.A)} > M={self.M}"
        )  # noqa

        # First version of F
        self.F = [data.count(a) for a in self.A]

        M2 = sum(self.F)
        F2 = [int(max(1, (f * (self.M / M2)))) for f in self.F]

        # Adjust F2 to ensure sum(F2) == M
        while sum(F2) < self.M:
            i = argmax([f - f2 for f, f2 in zip(self.F, F2)])
            F2[i] += 1
        while sum(F2) > self.M:
            i = argmax(F2)
            if F2[i] > 1:
                F2[i] -= 1
            else:
                break  # cannot reduce further

        assert sum(F2) == self.M, (
            f"Frequency table adjustment failed: sum(F)={sum(F2)} != M={self.M}"
        )  # noqa
        self.F = F2

        # Index = {a: i for i, a in enumerate(self.A)}
        # self.C: CDFType = [sum(self.F[: i]) for i in range(len(self.A))]
        self.C: CDFType = []
        cum = 0
        for f in self.F:
            self.C.append(cum)
            cum += f
        # self.C: CDFType = [sum(self.F[: i+1]) for i in range(len(self.A))]

        print("Alphabet:", self.A)
        print("Total Frequency M=", self.M)
        print("PMF:", [v for v in self.F])
        # print("PMF / M:", [float(v) / self.M for v in self.F])
        print("CDF:", [v for v in self.C])
        # print("CDF / M:", [float(v) / self.M for v in self.CDF])
        print(f"Renormalization base b={self.b}, L={self.L}, bL={self.bL}")

        assert self.C == [sum(self.F[:i]) for i in range(len(self.A))]

        if len(self.A) == 0:
            return ""

        x: int = self.L  # Initial state

        idx = self.A.index(data[0])

        encoded = ""

        def C(s: int, x: int) -> int:
            x_prev = x  # noqa
            idx = self.A.index(s)
            Fs = self.F[idx]
            Cs = self.C[idx]
            block_id = x // Fs
            slot = Cs + (x % Fs)
            # print(
            #     f"  Push {s} {ch(s)}: block_id={pr(block_id)} {slot=} {idx=} {Fs=} {Cs=}"
            # )  # noqa
            x = block_id * self.M + slot
            # print(f"   x : {pr(x_prev)} -> {pr(x)}  PUSH {ch(s)}")
            # print(
            #     f"   x = {x}  : x = {block_id * self.M=} + {slot=} = {block_id * self.M + slot}"
            # )
            # print(f"Encode X_{step} = {x}")
            return x

        def write_to_stream(bits: int) -> None:
            nonlocal encoded
            bits_str = format(bits, "b").zfill(self.k)
            encoded += bits_str
            # print(f"  Emit {bits} str={bits_str}")

        for step_, s in tqdm.tqdm(enumerate(data), desc="Encoding"):
            step = step_ + 1  # noqa
            # print("\nEncoding step:", step)

            # assert x < self.bL, f"Invalid state: x < bL={self.bL}, but x={x}"  # noqa
            assert self.L <= x < self.bL, (
                f"Invalid state: L={self.L} <= x < bL={self.bL}, but x={x}"
            )  # noqa

            idx = self.A.index(s)
            Fs = self.F[idx]

            # renormalization
            x_max = (self.b * (self.L // self.M)) * Fs
            # print(f"  Before push: x={pr(x)}, Fs={Fs}, x_max={pr(x_max)}")
            while x >= x_max:
                # print(f"  Renormalize: {x=} >= {x_max=}")
                bits = x % self.b  # noqa
                bits_str = format(bits, "b").zfill(self.k)  # noqa

                write_to_stream(x % self.b)
                x >>= self.k
                # print(
                #     f"  Renormalize: (∵ x={x_prev} >= {x_max=}）: emit {x % self.b} str={bits_str}, new x={pr(x)}"  # noqa
                # )

            x = C(s, x)

        # print(f"Final state x={pr(x)}")
        encoded = "_".join([str(len(data)), str(x), encoded])
        # print(f"Encoded : {encoded}")

        return encoded

    def decode(self, encoded: str) -> bytes:
        decoded = bytearray()

        l_str, x_str, body_str = encoded.split("_")
        length: int = int(l_str)
        x = int(x_str)

        if length == 0:
            return bytes(decoded[::-1])

        assert len(body_str) % self.k == 0

        # print("Decoding: initial state x=", pr(x))

        def D(x) -> tuple[int, int]:
            r, slot = divmod(x, self.M)
            pop_i, Cs, Fs = self.pop_s(slot)
            s = self.A[pop_i]
            x = r * Fs + slot - Cs
            return s, x

        def read_from_stream() -> int:
            nonlocal body_str
            # print(f"  Renormalize: {x=} < L={self.L}")
            bits_str = body_str[-self.k :]
            bits = int(bits_str, 2)
            body_str = body_str[: -self.k]
            # print(f"  Renormalize: read {bits_str} = {bits}, new x={pr(x)}")
            return bits

        for step_ in tqdm.tqdm(range(length), desc="Decoding"):
            step = step_ + 1  # noqa
            # print("\nDecoding step:", step)

            assert self.L <= x < self.bL, (
                f"Invalid state: L={self.L} <= x < {self.bL}, but x={x}"
            )  # noqa

            s, x = D(x)
            decoded.append(s)

            while x < self.L:
                x = x * self.b + read_from_stream()

        # print("\nDecoding state history:")
        return bytes(decoded[::-1])  # Reverse the decoded data

    def pop_s(self, slot) -> tuple[int, int, int]:
        for i in range(len(self.F)):
            Cs = self.C[i]
            Fs = self.F[i]
            # U = self.CDF[i + 1] if i + 1 < len(self.CDF) else self.M
            # print(
            #     f"  {i=}, {Cs=}, {Fs=} c={self.CDF[i]} s={self.A[i]} {ch(self.A[i])}"
            # )
            if Cs <= slot < Cs + Fs:
                s = self.A[i]  # noqa
                # print(
                #     f"  ==> Found slot for symbol! index {i}: {s=} '{ch(s)}' {Cs=} {Fs=} [{Cs}, {Cs + Fs})"
                # )  # noqa
                return i, Cs, Fs
        raise RuntimeError(f"Decoding failed: slot {slot} not found in CDF")
