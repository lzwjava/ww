"""Tanh (Hyperbolic Tangent) — Comprehensive CLI reference tool"""

import math
import os
import sys
import tempfile

# ── Colors / Styles
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[92m"
_CYAN = "\033[96m"
_YELLOW = "\033[93m"
_RED = "\033[91m"
_MAGENTA = "\033[95m"
_RESET = "\033[0m"


def _style(text: str, *codes: str) -> str:
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + _RESET


# ── Core Math Functions


def tanh(x: float) -> float:
    return math.tanh(x)


def tanh_derivative(x: float) -> float:
    t = math.tanh(x)
    return 1 - t * t


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


# ── Plotting


def _plot_tanh():
    """Generate and open a matplotlib figure showing tanh and its derivative."""
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("Error: matplotlib is required for plotting.")
        print("Install it with: pip install matplotlib")
        sys.exit(1)

    import numpy as np

    x = np.linspace(-5, 5, 1000)
    y = np.tanh(x)
    dy = 1 - np.tanh(x) ** 2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # Left: tanh(x)
    ax1.plot(x, y, label="tanh(x)", linewidth=2, color="#1f77b4")
    ax1.axhline(0, color="k", linewidth=0.5)
    ax1.axvline(0, color="k", linewidth=0.5)
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_title("tanh activation", fontsize=12, fontweight="bold")
    ax1.set_xlabel("x", fontsize=11)
    ax1.set_ylabel("tanh(x)", fontsize=11)
    ax1.set_xlim(-5.5, 5.5)
    ax1.set_ylim(-1.1, 1.1)

    # Right: derivative
    ax2.plot(x, dy, label=r"$1 - \tanh^2(x)$", linewidth=2, color="orange")
    ax2.axhline(0, color="k", linewidth=0.5)
    ax2.axvline(0, color="k", linewidth=0.5)
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_title("tanh derivative", fontsize=12, fontweight="bold")
    ax2.set_xlabel("x", fontsize=11)
    ax2.set_ylabel("gradient", fontsize=11)
    ax2.set_xlim(-5.5, 5.5)
    ax2.set_ylim(-0.1, 1.1)

    fig.tight_layout()

    # Save to temp file and open
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    fig.savefig(tmp.name, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Figure saved: {tmp.name}")
    if sys.platform == "darwin":
        os.system(f"open {tmp.name}")
    elif sys.platform == "linux":
        os.system(f"xdg-open {tmp.name} 2>/dev/null || see {tmp.name}")
    else:
        os.system(f"start {tmp.name}")


# ── Table & Data Printing


def _print_value_table(values: list[float]):
    h = f"{'x':>8}  {'tanh(x)':>12}  {'Derivative':>12}  {'Sigmoid(x)':>12}  {'tanh from sigmoid':>18}"
    sep = "\u2500" * len(h)
    print(f"\n  {_style('Tanh Value Table', _BOLD, _CYAN)}")
    print(f"  {_style(sep, _DIM)}")
    print(f"  {h}")
    print(f"  {_style(sep, _DIM)}")
    for x in values:
        t = tanh(x)
        d = tanh_derivative(x)
        s = sigmoid(x)
        ts = 2 * s - 1
        print(f"  {x:>8.3f}  {t:>+12.8f}  {d:>+12.8f}  {s:>+12.8f}  {ts:>+18.8f}")
    print(f"  {_style(sep, _DIM)}")
    print(f"  {'x=0':>8}  {_style('1.00000000', _GREEN, _BOLD):>12}  (Sigmoid: 0.25)")
    print()


def _print_properties():
    props = [
        ("Output Range", "(-1, 1)"),
        ("Zero-Centered", "Yes (mean output = 0)"),
        ("Odd Function", "tanh(-x) = -tanh(x)"),
        ("Derivative", "d/dx tanh(x) = 1 - tanh\u00b2(x)"),
        ("Derivative @ x=0", _style("1", _GREEN, _BOLD) + " (Sigmoid: 0.25)"),
        ("Monotonic", "Strictly increasing"),
        ("Saturation", "|x| > 3 \u2192 \u00b11, gradient \u2248 0"),
    ]
    print(f"  {_style('Key Properties', _BOLD, _CYAN)}")
    for k, v in props:
        print(f"    {_style(k + ':', _YELLOW):>20}  {v}")
    print()


def _print_formula():
    print(f"  {_style('Mathematical Definition', _BOLD, _CYAN)}")
    print("    tanh(x) = (e^x - e^-x) / (e^x + e^-x) = sinh(x) / cosh(x)")
    print()
    print(f"  {_style('Relationship with Sigmoid', _BOLD, _CYAN)}")
    print("    tanh(x) = 2 \u00b7 \u03c3(2x) - 1    where \u03c3(x) = 1 / (1 + e^-x)")
    print()
    print(f"  {_style('Derivative Derivation', _BOLD, _CYAN)}")
    print("    d/dx tanh(x) = 1 - tanh\u00b2(x)")
    print("    \u2192 Derivative expressed in terms of the function itself")
    print()


def _print_comparison():
    print(f"  {_style('Tanh vs Sigmoid vs ReLU', _BOLD, _CYAN)}")
    rows = [
        ("Dimension", "Tanh", "Sigmoid", "ReLU"),
        ("Output Range", "(-1, 1)", "(0, 1)", "[0, \u221e)"),
        ("Zero-Centered", "Yes", "No", "No"),
        ("Vanishing Grad.", "Yes (large |x|)", "Yes (worse)", "No (x > 0)"),
        ("Derivative @ x=0", "1", "0.25", "1 (right)"),
        ("Speed", "Slow (exp)", "Slow (exp)", "Fast (threshold)"),
        ("Dying Neurons", "No", "No", "Yes (x < 0)"),
        ("Primary Use", "LSTM / GRU", "Binary output", "CNN / MLP"),
    ]
    cw = [max(len(r[i]) for r in rows) for i in range(4)]
    sep = "\u2500" * (sum(cw) + 3 * 3)
    print(f"  {_style(sep, _DIM)}")
    for i, row in enumerate(rows):
        line = "  ".join(f"{col:<{cw[j]}}" for j, col in enumerate(row))
        if i == 0:
            print(f"  {_style(line, _BOLD)}")
            print(f"  {_style(sep, _DIM)}")
        else:
            print(f"  {line}")
    print(f"  {_style(sep, _DIM)}")
    print()


def _print_applications():
    print(f"  {_style('Deep Learning Applications', _BOLD, _CYAN)}")
    apps = [
        ("LSTM / GRU", "Candidate hidden state & cell state updates"),
        ("RNN", "Default activation before modern architectures"),
        ("Feedforward (pre-2010)", "Preferred hidden-layer activation before ReLU"),
        ("Regression Output", "Natural choice when targets are in (-1, 1)"),
    ]
    block = "\u25a0"
    dash = "\u2014"
    for k, v in apps:
        print(f"    {_style(block, _GREEN)} {_style(k, _YELLOW)} {dash} {v}")
    print()


def _print_code_snippets():
    print(f"  {_style('Code Implementations', _BOLD, _CYAN)}")
    print()
    print(f"  {_style('Python / NumPy', _GREEN)}")
    print("    import numpy as np")
    print("    x = np.array([-2, -1, 0, 1, 2])")
    print("    y = np.tanh(x)                     # forward")
    print("    dy = 1 - y**2                      # derivative")
    print()
    print(f"  {_style('PyTorch', _GREEN)}")
    print("    import torch, torch.nn as nn")
    print("    x = torch.randn(32, 128)")
    print("    y = torch.tanh(x)                  # functional")
    print("    tanh_layer = nn.Tanh(); y = tanh_layer(x)  # module")
    print()
    print(f"  {_style('TensorFlow / Keras', _GREEN)}")
    print("    import tensorflow as tf")
    print("    x = tf.random.normal([32, 128])")
    print("    y = tf.tanh(x)")
    print("    # Or specify in a layer:")
    print("    tf.keras.layers.Dense(256, activation='tanh')")
    print()


def _print_summary():
    summary_bar = "\u2501\u2501\u2501 Summary \u2501\u2501\u2501"

    print(f"  {_style(summary_bar, _BOLD, _MAGENTA)}")
    print(
        f"  {_style('Tanh is a zero-centered upgrade of Sigmoid', _BOLD)}, "
        "outputting values in (-1, 1) with a mean of 0."
    )
    print(
        "  It solves the biased gradient issue caused by Sigmoid's strictly positive output."
    )
    print()
    print(
        f"  {_style('Today, ReLU-family activations dominate FFN and CNN', _DIM)}, but"
    )
    print(
        f"  {_style('Tanh remains irreplaceable in recurrent architectures (LSTM, GRU)', _BOLD, _GREEN)}\u2014"
    )
    print("  its symmetry enables natural signal flow within gating mechanisms.")
    print()
    print(f"  {_style('Bottom line: LSTM depends on tanh.', _BOLD, _CYAN)}")
    print()


# ── CLI Entry


def print_help():
    print("Usage: ww math tanh [options]")
    print()
    print("Tanh (Hyperbolic Tangent) - Neural network activation function reference")
    print()
    print("Options:")
    print(
        "  --plot, -p  Generate and open a matplotlib figure of tanh & its derivative"
    )
    print("  --values    Show Tanh value table (default key points)")
    print(
        "  --all       Show full info (formula + properties + table + comparison + code + summary)"
    )
    print("  --help, -h  Show this help")


def _parse_custom_values():
    custom = []
    for a in sys.argv[1:]:
        if a.startswith("-") and a[1:].isalpha():
            continue
        try:
            custom.append(float(a))
        except ValueError:
            pass
    return custom if custom else None


def cmd_tanh():
    show_plot = "--plot" in sys.argv or "-p" in sys.argv
    show_all = "--all" in sys.argv
    show_values = "--values" in sys.argv
    show_help = "--help" in sys.argv or "-h" in sys.argv

    if show_help:
        print_help()
        return

    # If --plot is given, generate the figure and exit
    if show_plot:
        _plot_tanh()
        return

    custom_values = _parse_custom_values()
    default_points = [-5, -3, -2, -1, -0.5, 0, 0.5, 1, 2, 3, 5]

    box_top = "\u2554" + "\u2550" * 42 + "\u2557"
    box_bot = "\u255a" + "\u2550" * 42 + "\u255d"
    title = "\u2551          Tanh \u00b7 Hyperbolic Tangent            \u2551"

    print()
    print(f"  {_style(box_top, _CYAN)}")
    print(f"  {_style(title, _CYAN, _BOLD)}")
    print(f"  {_style(box_bot, _CYAN)}")
    print()

    values = custom_values if custom_values else default_points

    if show_all:
        _print_formula()
        _print_properties()
        _print_value_table(values)
        _print_comparison()
        _print_applications()
        _print_code_snippets()
        _print_summary()
    elif show_values:
        _print_value_table(values)
    else:
        _print_formula()
        _print_properties()
        _print_value_table(values)
        _print_comparison()
        _print_summary()


def main():
    cmd_tanh()
