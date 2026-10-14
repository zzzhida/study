import csv
import argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description="Draw waveforms from csv")
parser.add_argument("-i", "--input", required=True, help="csv 文件")
parser.add_argument("-o", "--output", required=True, help="输出图片 (.png)")
parser.add_argument("-t", "--tend", type=float, default=None, help="仿真结束时间 ($finish 的时刻)")
parser.add_argument("-s", "--signals", nargs="*", default=None,
                    help="要画的信号, 默认画 testbench 顶层的信号")
args = parser.parse_args()

with open(args.input, newline="", encoding="utf-8") as f:
    rows = list(csv.reader(f))
head, data = rows[0], rows[1:]
times = [float(r[0]) for r in data]

if args.signals:
    names = [n for n in head[1:]
             if n.count(".") == 1 and n.split(".")[-1] in args.signals]
    names.sort(key=lambda n: args.signals.index(n.split(".")[-1]))
else:
    names = [n for n in head[1:] if n.count(".") == 1]

tend = args.tend if args.tend else times[-1] + (times[-1] - times[-2])
fig, axes = plt.subplots(len(names), 1, sharex=True, figsize=(8, 1.0 * len(names) + 0.8))
for ax, name in zip(axes, names):
    col = head.index(name)
    vals = [1 if r[col] == "1" else 0 for r in data]
    ax.step(times + [tend], vals + [vals[-1]], where="post", linewidth=1.5)
    ax.set_ylim(-0.3, 1.3)
    ax.set_yticks([0, 1])
    ax.set_ylabel(name.split(".")[-1], rotation=0, ha="right", va="center")
    ax.grid(axis="x", linestyle=":")
axes[-1].set_xlabel("time (ns)")
axes[-1].set_xlim(0, tend)
plt.tight_layout()
plt.savefig(args.output, dpi=200)
print("saved", args.output)
