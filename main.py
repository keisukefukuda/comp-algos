import math
import sys

sys.path.insert(0, "python")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from algorithms.rans import RANS

M = 4096
k = 8       # b = 2^k = 256
b = 1 << k

rans = RANS()
ns = list(range(1, 1025))

# --- 2シンボル版 ---
F_2 = [1, M - 1]

output_bytes_2 = []
for n in ns:
    data = bytes([0] * n)
    encoded = rans.encode(data, freq_table=F_2, num_symbols=2)
    output_bytes_2.append(math.ceil(len(encoded.data) / 8))

# --- 64シンボル版 ---
NUM_SYMBOLS = 64
F_64 = [0] * NUM_SYMBOLS
F_64[0] = 1
for i in range(1, NUM_SYMBOLS):
    F_64[i] = (M - 1) // (NUM_SYMBOLS - 1)
while sum(F_64) < M:
    F_64[-1] += 1
F_64[1] += M - sum(F_64)

output_bytes_64 = []
for n in ns:
    data = bytes([0] * n)
    encoded = rans.encode(data, freq_table=F_64, num_symbols=NUM_SYMBOLS)
    output_bytes_64.append(math.ceil(len(encoded.data) / 8))

# 参考曲線: N * ceil(log_b(M))
log_bM = math.log(M, b)   # ceil(log_256(4096)) = 2
print(f"log_bM = {log_bM}")
ref_curve = [n * log_bM for n in ns]

# 比率: output_bytes / N
ratio_2  = [b / n for b, n in zip(output_bytes_2,  ns)]
ratio_64 = [b / n for b, n in zip(output_bytes_64, ns)]
ref_ratio = [log_bM] * len(ns)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))

# プロット1: 出力バイト数
ax1.plot(ns, output_bytes_2,  label="2 symbols  (RANS output)")
ax1.plot(ns, output_bytes_64, label="64 symbols (RANS output)")
ax1.plot(ns, ref_curve, label=f"N × log_b(M) = N × {log_bM}", linestyle="--")
ax1.set_xlabel("Input length N")
ax1.set_ylabel("Output size (bytes)")
ax1.set_title("Worst-case RANS output size (wrong freq table)")
ax1.legend()

# プロット2: 出力バイト数 / 入力記号長
ax2.plot(ns, ratio_2,  label="2 symbols  (output / N)")
ax2.plot(ns, ratio_64, label="64 symbols (output / N)")
ax2.plot(ns, ref_ratio, label=f"log_b(M) = {log_bM}", linestyle="--")
ax2.set_xlabel("Input length N")
ax2.set_ylabel("Output size / Input length (bytes/symbol)")
ax2.set_title("Output-to-input ratio")
ax2.legend()

plt.tight_layout()
plt.savefig("output.png")
print("Saved: output.png")
