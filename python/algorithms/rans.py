import tqdm  # noqa
from typing import Any

from algorithms.abc import Compresssor, PMFType, CDFType, AlphabetType


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
    def __init__(self) -> None:
        pass

    def prepare_frequency_table(
        self, data: bytes, M: int
    ) -> tuple[AlphabetType, PMFType, CDFType]:
        A: AlphabetType = sorted(list(set(data)))
        assert len(A) <= M, f"Alphabet size too large: |A|={len(A)} > M={M}"  # noqa

        # First version of F
        F: PMFType = [data.count(a) for a in A]

        M2 = sum(F)
        F2: PMFType = [int(max(1, (f * (M / M2)))) for f in F]
        # Adjust F2 to ensure sum(F2) == M
        while sum(F2) < M:
            i = argmax([f - f2 for f, f2 in zip(F, F2)])
            F2[i] += 1
        while sum(F2) > M:
            i = argmax(F2)
            if F2[i] > 1:
                F2[i] -= 1
            else:
                break  # cannot reduce further

        assert sum(F2) == M, f"Freq table adjustment failed: sum(F)={sum(F2)} != M={M}"  # noqa
        F = F2

        # Index = {a: i for i, a in enumerate(A)}
        # C: CDFType = [sum(F[: i]) for i in range(len(A))]
        C: CDFType = []
        cum = 0
        for f in F:
            C.append(cum)
            cum += f
        assert C == [sum(F[:i]) for i in range(len(A))]

        return A, F, C

    def encode(self, data: bytes) -> dict[str, Any]:
        # Setup hyper parameters

        assert type(data) is bytes
        if len(data) == 0:
            return {"data": "", "meta": {"length": 0}}

        k: int = 8
        b: int = 1 << k
        L: int = 2**23
        bL: int = b * L
        M: int = 4096

        assert L > M and L % M == 0
        assert L >= b and L % b == 0

        meta: dict[str, Any] = {"k": k, "b": b, "L": L, "bL": bL, "M": M}

        A, F, C = self.prepare_frequency_table(data, M)

        print("Alphabet:", A)
        print("Total Frequency M=", M)
        print("PMF:", [v for v in F])
        # print("PMF / M:", [float(v) / M for v in F])
        print("CDF:", [v for v in C])
        # print("CDF / M:", [float(v) / M for v in C])
        print(f"Renormalization base b={b}, L={L}, bL={bL}")

        if len(A) == 0:
            return {"data": "", "meta": {}}

        x: int = L  # Initial state

        idx = A.index(data[0])

        encoded = ""

        def get_C(s: int, x: int) -> int:
            x_prev = x  # noqa
            idx = A.index(s)
            Fs = F[idx]
            Cs = C[idx]
            block_id = x // Fs
            slot = Cs + (x % Fs)
            # print(
            #     f"  Push {s} {ch(s)}: block_id={pr(block_id)} {slot=} {idx=} {Fs=} {Cs=}"  # noqa
            # )  # noqa
            x = block_id * M + slot
            # print(f"   x : {pr(x_prev)} -> {pr(x)}  PUSH {ch(s)}")
            # print(
            #     f"   x = {x}  : x = {block_id * M=} + {slot=} = {block_id * M + slot}"  # noqa
            # )
            # print(f"Encode X_{step} = {x}")
            return x

        def write_to_stream(bits: int) -> None:
            nonlocal encoded
            bits_str = format(bits, "b").zfill(k)
            encoded += bits_str
            # print(f"  Emit {bits} str={bits_str}")

        for step_, s in tqdm.tqdm(enumerate(data), desc="Encoding"):
            step = step_ + 1  # noqa
            # print("\nEncoding step:", step)

            # assert x < bL, f"Invalid state: x < bL={bL}, but x={x}"  # noqa
            assert L <= x < bL, f"Invalid state: L={L} <= x < bL={bL}, but x={x}"  # noqa

            idx = A.index(s)
            Fs = F[idx]

            # renormalization
            x_max = (b * (L // M)) * Fs
            # print(f"  Before push: x={pr(x)}, Fs={Fs}, x_max={pr(x_max)}")
            while x >= x_max:
                # print(f"  Renormalize: {x=} >= {x_max=}")
                bits = x % b  # noqa
                bits_str = format(bits, "b").zfill(k)  # noqa

                write_to_stream(x % b)
                x >>= k
                # print(
                #     f"  Renormalize: (∵ x={x_prev} >= {x_max=}）: emit {x % b} str={bits_str}, new x={pr(x)}"  # noqa
                # )

            x = get_C(s, x)

        # print(f"Final state x={pr(x)}")
        # encoded = "_".join([str(len(data)), str(x), encoded])
        # print(f"Encoded : {encoded}")

        meta = {
            "A": A,
            "length": len(data),
            "state": x,  # final state
            "k": k,
            "L": L,
            "b": b,
            "M": M,
            "F": F,
            "C": C,
        }

        ret: dict[str, Any] = {
            "data": encoded,
            "meta": meta,
        }

        return ret

    def decode(self, encoded: dict[str, Any]) -> bytes | bytearray:
        decoded = bytearray()

        meta = encoded["meta"]

        length: int = meta["length"]
        if length == 0:
            return b""

        x = meta["state"]
        body_str = encoded["data"]
        A: AlphabetType = meta["A"]
        k: int = int(meta["k"])
        L: int = int(meta["L"])
        b: int = int(meta["b"])
        M: int = int(meta["M"])
        F: PMFType = meta["F"]
        C: CDFType = meta["C"]

        assert len(body_str) % k == 0, f"{len(body_str)} % {k} != 0, {body_str=}"
        # assert type(F) is PMFType, f"{type(F)} != PMFType"
        # assert type(A) is AlphabetType, f"{type(A)} != AlphabetType"
        # assert type(C) is CDFType, f"{type(C)} != CDFType"

        # print("Decoding: initial state x=", pr(x))

        def D(x) -> tuple[int, int]:
            r, slot = divmod(x, M)
            pop_i, Cs, Fs = self.pop_s(slot, A, F, C)
            s = A[pop_i]
            x = r * Fs + slot - Cs
            return s, x

        def read_from_stream() -> int:
            nonlocal body_str
            # print(f"  Renormalize: {x=} < L={L}")
            bits_str = body_str[-k:]
            bits = int(bits_str, 2)
            body_str = body_str[:-k]
            # print(f"  Renormalize: read {bits_str} = {bits}, new x={pr(x)}")
            return bits

        for step_ in tqdm.tqdm(range(length), desc="Decoding"):
            step = step_ + 1  # noqa
            # print("\nDecoding step:", step)

            assert L <= x < b * L, f"Invalid state: L={L} <= x < {b * L}, but x={x}"  # noqa

            s, x = D(x)
            decoded.append(s)

            while x < L:
                x = x * b + read_from_stream()
        # print("\nDecoding state history:")
        return bytes(decoded[::-1])  # Reverse the decoded data

    def pop_s(self, slot, A, F, C) -> tuple[int, int, int]:
        for i in range(len(F)):
            Cs = C[i]
            Fs = F[i]
            # U = C[i + 1] if i + 1 < len(C) else M
            # print(
            #     f"  {i=}, {Cs=}, {Fs=} c={C[i]} s={A[i]} {ch(A[i])}"  # noqa
            # )
            if Cs <= slot < Cs + Fs:
                s = A[i]  # noqa
                # print(
                #     f"  ==> Found slot for symbol! index {i}: {s=} '{ch(s)}' {Cs=} {Fs=} [{Cs}, {Cs + Fs})"  # noqa
                # )  # noqa
                return i, Cs, Fs
        raise RuntimeError(f"Decoding failed: slot {slot} not found in CDF")
