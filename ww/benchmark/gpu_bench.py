#!/usr/bin/env python3
"""GPU Benchmark — tensor compute, memory bandwidth, mixed precision.

Supports NVIDIA GPUs with CUDA via PyTorch.
Tests: FP32/TF32/FP16/BF16/FP8 matmul, memory bandwidth, transformer-like workloads.
"""

import os
import sys
import time

# Theoretical peaks per GPU (dense, tensor cores, boost clocks)
# These are approximate — actual silicon varies by SKU and cooling.
THEORETICAL_PEAKS = {
    # Dense tensor core peaks (boost clocks, not sparse)
    "NVIDIA B200": {
        "FP32": 67,
        "TF32": 740,
        "FP16": 2250,
        "BF16": 2250,
        "FP8": 4500,
        "FP4": 9000,
        "mem_bw": 8000,
    },
    "NVIDIA H200 SXM": {
        "FP32": 67,
        "TF32": 740,
        "FP16": 1979,
        "BF16": 1979,
        "FP8": 3958,
        "FP4": 7916,
        "mem_bw": 4800,
    },
    "NVIDIA H100 SXM": {
        "FP32": 67,
        "TF32": 740,
        "FP16": 989,
        "BF16": 989,
        "FP8": 1979,
        "FP4": 3958,
        "mem_bw": 3350,
    },
    "NVIDIA A100 SXM": {
        "FP32": 19.5,
        "TF32": 156,
        "FP16": 312,
        "BF16": 312,
        "FP8": 312,
        "FP4": 312,
        "mem_bw": 2039,
    },
    "NVIDIA RTX 4090": {
        "FP32": 4.3,
        "TF32": 16.6,
        "FP16": 33.2,
        "BF16": 33.2,
        "FP8": 66.4,
        "FP4": 132.8,
        "mem_bw": 1008,
    },
}

# Collect results for summary
results = {}


def banner(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def bench(name, fn, warmup=5, iters=50):
    """Benchmark a function, return average ms."""
    for _ in range(warmup):
        fn()
    torch.cuda.synchronize()
    start = time.time()
    for _ in range(iters):
        fn()
    torch.cuda.synchronize()
    elapsed = time.time() - start
    avg_ms = elapsed / iters * 1000
    print(f"  {name:45s}  {avg_ms:8.3f} ms  (x{iters})")
    return avg_ms


def tflops_val(flops, avg_ms):
    """Compute TFLOPS from FLOP count and avg latency in ms."""
    return flops / (avg_ms / 1000) / 1e12


def run_benchmark():
    global torch
    import torch

    banner("SYSTEM INFO")
    gpu_name = torch.cuda.get_device_name(0)
    props = torch.cuda.get_device_properties(0)
    print(f"  PyTorch:       {torch.__version__}")
    print(f"  CUDA:          {torch.version.cuda}")
    print(f"  GPU:           {gpu_name}")
    mem_gb = props.total_memory / 1024**3
    print(f"  Memory:        {mem_gb:.1f} GB")
    print(f"  SMs:           {props.multi_processor_count}")
    print(f"  Compute cap:   {props.major}.{props.minor}")
    print(f"  BF16 support:  {torch.cuda.is_bf16_supported()}")

    peaks = THEORETICAL_PEAKS.get(gpu_name, {})

    # ── 1. FP32 MatMul (CUDA cores, no tensor) ──────────────────
    banner("FP32 MATMUL (CUDA cores)")
    torch.backends.cuda.matmul.allow_tf32 = False
    fp32_best, fp32_best_n = 0, 0
    for n in [1024, 2048, 4096, 8192, 16384]:
        a = torch.randn(n, n, device="cuda", dtype=torch.float32)
        b = torch.randn(n, n, device="cuda", dtype=torch.float32)
        iters = max(5, 200 // (n // 1024))
        avg = bench(f"{n}x{n}", lambda: torch.mm(a, b), warmup=3, iters=iters)
        t = tflops_val(2 * n**3, avg)
        if t > fp32_best:
            fp32_best, fp32_best_n = t, n
        print(f"{'':45s}  => {t:.1f} TFLOPS")
    results["FP32"] = (fp32_best, fp32_best_n)

    # ── 2. TF32 MatMul (tensor cores, FP32 data) ────────────────
    banner("TF32 MATMUL (tensor cores, FP32 I/O)")
    torch.backends.cuda.matmul.allow_tf32 = True
    tf32_best, tf32_best_n = 0, 0
    for n in [4096, 8192, 16384]:
        a = torch.randn(n, n, device="cuda", dtype=torch.float32)
        b = torch.randn(n, n, device="cuda", dtype=torch.float32)
        iters = max(5, 200 // (n // 1024))
        avg = bench(f"{n}x{n}", lambda: torch.mm(a, b), warmup=3, iters=iters)
        t = tflops_val(2 * n**3, avg)
        if t > tf32_best:
            tf32_best, tf32_best_n = t, n
        print(f"{'':45s}  => {t:.1f} TFLOPS")
    results["TF32"] = (tf32_best, tf32_best_n)

    # ── 3. FP16 MatMul (tensor cores) ───────────────────────────
    banner("FP16 MATMUL (tensor cores)")
    fp16_best, fp16_best_n = 0, 0
    for n in [1024, 2048, 4096, 8192, 16384]:
        a = torch.randn(n, n, device="cuda", dtype=torch.float16)
        b = torch.randn(n, n, device="cuda", dtype=torch.float16)
        iters = max(10, 500 // (n // 1024))
        avg = bench(f"{n}x{n}", lambda: torch.mm(a, b), warmup=5, iters=iters)
        t = tflops_val(2 * n**3, avg)
        if t > fp16_best:
            fp16_best, fp16_best_n = t, n
        print(f"{'':45s}  => {t:.1f} TFLOPS")
    results["FP16"] = (fp16_best, fp16_best_n)

    # ── 4. BF16 MatMul (tensor cores) ───────────────────────────
    banner("BF16 MATMUL (tensor cores)")
    bf16_best, bf16_best_n = 0, 0
    for n in [1024, 2048, 4096, 8192, 16384]:
        a = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        b = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        iters = max(10, 500 // (n // 1024))
        avg = bench(f"{n}x{n}", lambda: torch.mm(a, b), warmup=5, iters=iters)
        t = tflops_val(2 * n**3, avg)
        if t > bf16_best:
            bf16_best, bf16_best_n = t, n
        print(f"{'':45s}  => {t:.1f} TFLOPS")
    results["BF16"] = (bf16_best, bf16_best_n)

    # ── 5. FP8 MatMul (scaled_mm) ───────────────────────────────
    banner("FP8 MATMUL (torch._scaled_mm)")
    fp8_best, fp8_best_n = 0, 0
    fp8_ok = False
    try:
        for n in [1024, 2048, 4096, 8192, 16384]:
            a = torch.randn(n, n, device="cuda", dtype=torch.float8_e4m3fn)
            b = torch.randn(n, n, device="cuda", dtype=torch.float8_e4m3fn).t()
            scale_a = torch.ones(1, device="cuda", dtype=torch.float32)
            scale_b = torch.ones(1, device="cuda", dtype=torch.float32)
            iters = max(10, 500 // (n // 1024))

            def fp8_mm():
                return torch._scaled_mm(a, b, scale_a=scale_a, scale_b=scale_b)

            avg = bench(f"{n}x{n}", fp8_mm, warmup=5, iters=iters)
            t = tflops_val(2 * n**3, avg)
            if t > fp8_best:
                fp8_best, fp8_best_n = t, n
            print(f"{'':45s}  => {t:.1f} TFLOPS")
            fp8_ok = True
    except Exception as e:
        print(f"  FP8 not available: {e}")
        fp8_best = 0
    results["FP8"] = (fp8_best, fp8_best_n, fp8_ok)

    # ── 6. Memory Bandwidth ─────────────────────────────────────
    banner("MEMORY BANDWIDTH (elementwise x*2, read+write)")
    best_bw = 0
    for size_mb in [64, 256, 1024, 4096, 8192, 16384]:
        n = size_mb * 1024 * 1024 // 4  # float32 elements
        x = torch.randn(n, device="cuda")
        iters = max(5, 200 // max(1, size_mb // 64))
        avg = bench(f"Copy {size_mb} MB", lambda: x * 2.0, warmup=3, iters=iters)
        bw = 2 * size_mb / 1024 / (avg / 1000)  # read + write, GB/s
        if bw > best_bw:
            best_bw = bw
        print(f"{'':45s}  => {bw:.1f} GB/s")
    results["MEM_BW"] = best_bw

    # ── 7. Transformer-Like Workloads (BF16) ────────────────────
    banner("TRANSFORMER-LIKE WORKLOADS (BF16)")
    shapes = [
        ("LLM prefill (B=1, S=2048, H=4096)", 2048, 4096, 4096),
        ("LLM prefill (B=1, S=4096, H=4096)", 4096, 4096, 4096),
        ("LLM prefill (B=1, S=8192, H=8192)", 8192, 8192, 8192),
        ("QKV proj (B=32, S=2048, d=4096)", 32 * 2048, 4096, 4096),
        ("QKV proj (B=32, S=4096, d=8192)", 32 * 4096, 8192, 8192),
        ("FFN up (B=32, S=2048, d=11008)", 32 * 2048, 11008, 4096),
        ("FFN up (B=32, S=4096, d=11008)", 32 * 4096, 11008, 4096),
        ("FFN down (B=32, S=2048, d=4096)", 32 * 2048, 4096, 11008),
        ("Attention logits (B=32, H=4096, S=4096)", 32 * 4096, 4096, 4096),
    ]
    transformer_results = []
    for label, M, N, K in shapes:
        a = torch.randn(M, K, device="cuda", dtype=torch.bfloat16)
        b = torch.randn(K, N, device="cuda", dtype=torch.bfloat16)
        avg = bench(label, lambda: torch.mm(a, b), warmup=3, iters=20)
        t = tflops_val(2 * M * N * K, avg)
        transformer_results.append((label, t))
        print(f"{'':45s}  => {t:.1f} TFLOPS")
    results["TRANSFORMER"] = transformer_results

    # ── 8. Latency Micro-Benchmarks ─────────────────────────────
    banner("LATENCY MICRO-BENCHMARKS (FP16, 1024x1024)")
    x = torch.randn(1024, 1024, device="cuda", dtype=torch.float16)
    y = torch.randn(1024, 1024, device="cuda", dtype=torch.float16)
    latency_ops = {}
    for name, fn in [
        ("add", lambda: x + y),
        ("mul", lambda: x * y),
        ("div", lambda: x / y),
        ("relu", lambda: torch.relu(x)),
        ("gelu", lambda: torch.nn.functional.gelu(x)),
        ("silu", lambda: torch.nn.functional.silu(x)),
        ("sigmoid", lambda: torch.sigmoid(x)),
        ("tanh", lambda: torch.tanh(x)),
        ("softmax", lambda: torch.softmax(x, dim=-1)),
        ("layer_norm", lambda: torch.nn.functional.layer_norm(x, (1024,))),
        ("rms_norm", lambda: torch.rsqrt(x * x + 1e-6) * x),
        (
            "dropout (eval)",
            lambda: torch.nn.functional.dropout(x, p=0.1, training=False),
        ),
        ("matmul 1024x1024", lambda: torch.mm(x, y)),
    ]:
        avg = bench(name, fn, warmup=100, iters=1000)
        latency_ops[name] = avg
    results["LATENCY"] = latency_ops

    # ── 9. Larger Tensor Sizes ───────────────────────────────────
    banner("SCALING TEST (BF16 matmul, increasing size)")
    for n in [512, 1024, 2048, 4096, 8192, 12288, 16384]:
        a = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        b = torch.randn(n, n, device="cuda", dtype=torch.bfloat16)
        iters = max(5, 500 // max(1, n // 1024))
        avg = bench(f"{n}x{n}", lambda: torch.mm(a, b), warmup=5, iters=iters)
        t = tflops_val(2 * n**3, avg)
        print(f"{'':45s}  => {t:.1f} TFLOPS")

    # ── 10. Print Summary ───────────────────────────────────────
    _print_summary(gpu_name, mem_gb, props.multi_processor_count, peaks)


def _print_summary(gpu_name, mem_gb, sm_count, peaks):
    """Print the final summary block."""
    banner(f"{gpu_name} BENCHMARK RESULTS")

    print()
    print("  TENSOR CORE MATMUL (the big numbers)")
    if "FP32" in results:
        t, n = results["FP32"]
        print(f"    FP32 (CUDA cores):  {t:>8.1f} TFLOPS @ {n}x{n}")
    if "TF32" in results:
        t, n = results["TF32"]
        print(f"    TF32 (tensor cores):{t:>8.1f} TFLOPS @ {n}x{n}")
    if "FP16" in results:
        t, n = results["FP16"]
        print(f"    FP16 (tensor cores):{t:>8.1f} TFLOPS @ {n}x{n}")
    if "BF16" in results:
        t, n = results["BF16"]
        print(f"    BF16 (tensor cores):{t:>8.1f} TFLOPS @ {n}x{n}")
    if "FP8" in results:
        t, n, ok = results["FP8"]
        if ok:
            print(f"    FP8  (tensor cores):{t:>8.1f} TFLOPS @ {n}x{n}")
        else:
            print(f"    FP8:  Not available (PyTorch {torch.__version__})")
            if peaks.get("FP8"):
                print(f"          Would expect ~{peaks['FP8']:.0f} TFLOPS on this GPU")

    # Efficiency vs theoretical
    if peaks:
        print()
        print(f"  Efficiency vs {gpu_name} theoretical peaks:")
        for dtype in ["FP32", "TF32", "FP16", "BF16", "FP8"]:
            if dtype in results and dtype in peaks:
                t = results[dtype][0]
                p = peaks[dtype]
                if t > 0:
                    eff = t / p * 100
                    bar_len = min(int(eff / 5), 40)
                    bar = "#" * bar_len + "." * max(0, 30 - bar_len)
                    print(
                        f"    {dtype:5s}: {t:>7,.0f} / {p:>5,.0f} TFLOPS  {bar} {eff:.0f}%"
                    )

    print()
    print("  MEMORY BANDWIDTH")
    if "MEM_BW" in results:
        bw = results["MEM_BW"]
        print(f"    Measured:    {bw:,.0f} GB/s")
        if peaks.get("mem_bw"):
            p = peaks["mem_bw"]
            eff = bw / p * 100
            print(f"    Theoretical: {p:,.0f} GB/s (HBM3)")
            print(f"    Efficiency:  {eff:.0f}%")

    if "TRANSFORMER" in results:
        print()
        print("  TRANSFORMER-LIKE WORKLOADS (BF16)")
        for label, t in results["TRANSFORMER"]:
            short = label.split("(")[0].strip()
            shape = label.split("(")[1].rstrip(")") if "(" in label else ""
            print(f"    {short:20s}  {t:>8,.0f} TFLOPS  ({shape})")

    if "LATENCY" in results:
        print()
        print("  ELEMENTWISE LATENCY (1024x1024 FP16, micro-ops)")
        for name, ms in results["LATENCY"].items():
            us = ms * 1000
            if us < 10:
                print(f"    {name:25s}  {us:6.1f} μs")
            else:
                print(f"    {name:25s}  {ms:6.3f} ms")

    print()
    print("  NOTES")
    print(f"    - PyTorch {torch.__version__}, CUDA {torch.version.cuda}")
    print(f"    - {sm_count} SMs, {mem_gb:.0f} GB VRAM")
    print("    - torch.mm() uses cuBLAS internally")
    print("    - FP32 results may use tensor cores via cuBLAS heuristics")
    print("    - Actual peak depends on matrix size, boost clocks,")
    print("      and tensor core pipeline saturation")
    if not peaks:
        print(f"    - No theoretical peak data for {gpu_name}")
        print("      (add to THEORETICAL_PEAKS dict in gpu_bench.py)")


def main():
    """Entry point for `ww benchmark`."""
    args = sys.argv[1:]

    if args and args[0] in ("--help", "-h", "help"):
        print("Usage: ww benchmark [options]")
        print()
        print("Run GPU benchmark on the current machine or a remote server.")
        print()
        print("Options:")
        print("  --ssh USER@HOST:PORT   Upload and run on a remote server via SSH")
        print("  --key PATH             SSH private key (default: ~/.ssh/id_ed25519)")
        print("  --help, -h             Show this help")
        return

    ssh_target = None
    ssh_key = os.path.expanduser("~/.ssh/id_ed25519")

    i = 0
    while i < len(args):
        if args[i] == "--ssh" and i + 1 < len(args):
            ssh_target = args[i + 1]
            i += 2
        elif args[i] == "--key" and i + 1 < len(args):
            ssh_key = args[i + 1]
            i += 2
        else:
            i += 1

    if ssh_target:
        _run_remote(ssh_target, ssh_key)
    else:
        _run_local()


def _run_local():
    """Run benchmark locally."""
    print("Running GPU benchmark locally...")
    try:
        run_benchmark()
    except ImportError:
        print("Error: PyTorch not found. Install with: pip install torch")
        sys.exit(1)
    except RuntimeError as e:
        if "CUDA" in str(e):
            print(f"CUDA error: {e}")
            print("No NVIDIA GPU available or CUDA not installed.")
        else:
            raise


def _run_remote(ssh_target: str, ssh_key: str):
    """Upload benchmark script to remote server and run it."""
    import subprocess
    import tempfile

    # Parse USER@HOST:PORT
    if ":" in ssh_target:
        host_part, port = ssh_target.rsplit(":", 1)
    else:
        host_part = ssh_target
        port = "22"

    # Build the benchmark script content
    script_path = os.path.join(os.path.dirname(__file__), "gpu_bench.py")
    with open(script_path) as f:
        script_content = f.read()

    ssh_base = [
        "ssh",
        "-p",
        port,
        "-i",
        os.path.expanduser(ssh_key),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
        host_part,
    ]

    scp_base = [
        "scp",
        "-P",
        port,
        "-i",
        os.path.expanduser(ssh_key),
        "-o",
        "StrictHostKeyChecking=no",
    ]

    # Write script to temp file, scp it, run it
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        tmp.write(script_content)
        tmp_path = tmp.name

    remote_path = "/tmp/ww_gpu_bench.py"
    try:
        print(f"Uploading benchmark to {ssh_target}...")
        r = subprocess.run(
            scp_base + [tmp_path, f"{host_part}:{remote_path}"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if r.returncode != 0:
            print(f"SCP failed: {r.stderr}")
            sys.exit(1)

        print(f"Running benchmark on {ssh_target}...\n")
        r = subprocess.run(
            ssh_base + [f"python3 {remote_path}"],
            timeout=600,
        )
        sys.exit(r.returncode)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    main()
