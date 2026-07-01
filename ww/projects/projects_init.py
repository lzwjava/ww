from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPOS_BASE = Path.home() / "projects"
CONFIG_PATH = Path(__file__).parent / "repos.json"

# Mapping of repo name → GitHub org/repo.
# If a repo name in repos.json already contains "/" it's used verbatim.
# Add entries here when the short name doesn't match the GitHub name or org.
NAME_TO_REPO: dict[str, str] = {
    # ai-models
    "DeepSeek-V3": "deepseek-ai/DeepSeek-V3",
    "DeepSeek-R1": "deepseek-ai/DeepSeek-R1",
    "DeepSeek-Coder-V2": "deepseek-ai/DeepSeek-Coder-V2",
    "Janus": "deepseek-ai/Janus",
    "Qwen3": "Qwen/Qwen3",
    "Qwen2.5-Coder": "Qwen/Qwen2.5-Coder",
    "Qwen2.5-VL": "Qwen/Qwen2.5-VL",
    "gpt-2": "openai/gpt-2",
    "CLIP": "openai/CLIP",
    "whisper-openai": "openai/whisper",
    "evals": "openai/evals",
    "llama3": "meta-llama/llama3",
    "Kimi-k1.5": "MoonshotAI/Kimi-k1.5",
    "Qwen2-Audio": "Qwen/Qwen2-Audio",
    "Qwen2.5-Math": "Qwen/Qwen2.5-Math",
    "llama": "meta-llama/llama",
    "gemma": "google-deepmind/gemma",
    "transformers": "huggingface/transformers",
    "whisper.cpp": "ggerganov/whisper.cpp",
    "MiMo": "menloresearch/MiMo",
    "GLM": "THUDM/GLM",
    "openfold": "aqlaboratory/openfold",
    # ai-training
    "pytorch": "pytorch/pytorch",
    "Megatron-LM": "NVIDIA/Megatron-LM",
    "nanoGPT": "karpathy/nanoGPT",
    "modded-nanogpt": "KellerJordan/modded-nanogpt",
    "llm.c": "karpathy/llm.c",
    "nanochat": "will-thompson-koder/nanochat",
    "bitsandbytes": "TimDettmers/bitsandbytes",
    "fairscale": "facebookresearch/fairscale",
    "fairseq": "facebookresearch/fairseq",
    "mistral-finetune": "mistralai/mistral-finetune",
    "diffusers": "huggingface/diffusers",
    "nanoVLM": "NanoVLM/nanoVLM",
    "open-r1": "huggingface/open-r1",
    "tutorials": "pytorch/tutorials",
    "ColossalAI": "hpcaitech/ColossalAI",
    "flash-attention": "Dao-AILab/flash-attention",
    "LlamaFactory": "hiyouga/LlamaFactory",
    "LLMs-from-scratch": "rasbt/LLMs-from-scratch",
    "minbpe": "karpathy/minbpe",
    "mamba": "state-spaces/mamba",
    "keras": "keras-team/keras",
    "simpletransformers": "ThilinaRajapakse/simpletransformers",
    "FlagEmbedding": "FlagOpen/FlagEmbedding",
    "trl": "huggingface/trl",
    "peft": "huggingface/peft",
    "torchtitan": "pytorch/torchtitan",
    "ao": "pytorch/ao",
    "minGPT": "karpathy/minGPT",
    "ng-video-lecture": "karpathy/ng-video-lecture",
    "triton": "triton-lang/triton",
    "jax": "jax-ml/jax",
    "DeepSpec": "deepseek-ai/DeepSpec",
    "sparse_attention": "openai/sparse_attention",
    "native-sparse-attention-triton": "ianlingo/native-sparse-attention-triton",
    # ai-inference
    "TensorRT-LLM": "NVIDIA/TensorRT-LLM",
    "dinov2": "facebookresearch/dinov2",
    "ggml": "ggml-org/ggml",
    "ktransformers": "kvcache-ai/ktransformers",
    "llama.cpp": "ggml-org/llama.cpp",
    "llamafile": "Mozilla-Ocho/llamafile",
    "mlx": "ml-explore/mlx",
    "mlx-examples": "ml-explore/mlx-examples",
    "nexa-sdk": "NexaAI/nexa-sdk",
    "nougat": "facebookresearch/nougat",
    "ollama": "ollama/ollama",
    "sglang": "sgl-project/sglang",
    "text-generation-webui": "oobabooga/text-generation-webui",
    "vllm": "vllm-project/vllm",
    "nano-vllm": "weedge/nano-vllm",
    # ai-apps
    "open-webui": "open-webui/open-webui",
    "dify": "langgenius/dify",
    "ComfyUI": "comfyanonymous/ComfyUI",
    "stable-diffusion-webui": "AUTOMATIC1111/stable-diffusion-webui",
    "langfuse": "langfuse/langfuse",
    "chatbox": "Bin-Huang/chatbox",
    "aider": "Aider-AI/aider",
    "LibreChat": "danny-avila/LibreChat",
    "litellm": "BerriAI/litellm",
    "anything-llm": "Mintplex-Labs/anything-llm",
    "Whisper": "openai/whisper",
    "facefusion": "facefusion/facefusion",
    "claude-relay-service": "mondayja/claude-relay-service",
    "voice-changer": "w-okada/voice-changer",
    "h2ogpt": "h2oai/h2ogpt",
    "langchain": "langchain-ai/langchain",
    "openai-cookbook": "openai/openai-cookbook",
    "anthropic-cookbook": "anthropics/anthropic-cookbook",
    "llama_index": "run-llama/llama_index",
    "mlflow": "mlflow/mlflow",
    "bark": "suno-ai/bark",
    "DaviRain-Su/empty": "DaviRain-Su/empty",
    # ai-agents
    "hermes-agent": "NousResearch/hermes-agent",
    "codex": "openai/codex",
    "claw-code": "clawcode/claw-code",
    "gpt-researcher": "assafelovic/gpt-researcher",
    "OpenHands": "All-Hands-AI/OpenHands",
    "autogen": "microsoft/autogen",
    "markitdown": "microsoft/markitdown",
    "browser-use": "browser-use/browser-use",
    "opencode": "opencode-ai/opencode",
    "gemini-cli": "google-gemini/gemini-cli",
    "claude-code": "anthropics/claude-code",
    "AutoGPT": "Significant-Gravitas/AutoGPT",
    "mem0": "mem0ai/mem0",
    "crewAI": "crewAIInc/crewAI",
    "langgraph": "langchain-ai/langgraph",
    "ORG2": "",  # placeholder — skip
    # dev-tools
    "git": "git/git",
    "react": "facebook/react",
    "terminal": "microsoft/terminal",
    "alacritty": "alacritty/alacritty",
    "uv": "astral-sh/uv",
    "nmap": "nmap/nmap",
    "warp": "warpdotdev/Warp",
    "iclaw": "iClaw/iclaw",
    "mcp": "modelcontextprotocol/mcp",
    "ROCm": "ROCm/ROCm",
    "Chat2DB": "chat2db/Chat2DB",
    "git-credential-manager": "git-ecosystem/git-credential-manager",
    "ChezScheme": "cisco/ChezScheme",
    "dubbo": "apache/dubbo",
    "coding-interview-university": "jwasham/coding-interview-university",
    "Bodhi-AI": "BodhiAI/Bodhi-AI",
    "Axono": "axonframework/AxonFramework",
    "fineract": "apache/fineract",
    "desktop": "Lojii/desktop",
    "lazygit": "jesseduffield/lazygit",
    "bat": "sharkdp/bat",
    "fd": "sharkdp/fd",
    "ripgrep": "BurntSushi/ripgrep",
    "zoxide": "ajeetdsouza/zoxide",
    "ruff": "astral-sh/ruff",
    "yazi": "sxyazi/yazi",
    "glow": "charmbracelet/glow",
    "delta": "dandavison/delta",
    "bun": "oven-sh/bun",
    "ramulator2": "CMU-SAFARI/ramulator2",
    "tiny-gpu": "adam-maj/tiny-gpu",
    "verilator": "verilator/verilator",
    "openlane2": "efabless/openlane2",
    "vortex": "EtiTheSpirit/vortex",
    "zed": "zed-industries/zed",
    "miu2d": "miu2d/miu2d",
    # infra-network
    "openwrt": "openwrt/openwrt",
    "searxng": "searxng/searxng",
    "shadowsocks-rust": "shadowsocks/shadowsocks-rust",
    "greptimedb": "GreptimeTeam/greptimedb",
    "netty": "netty/netty",
    "clash-core": "clash-core/clash-core",
    "mihomo": "MetaCubeX/mihomo",
    "chroma": "chroma-core/chroma",
    "qdrant": "qdrant/qdrant",
    "localGPT": "PromtEngineer/localGPT",
    "quivr": "QuivrHQ/quivr",
    "llm-app": "pathwaycom/llm-app",
    "v2rayN": "2dust/v2rayN",
    "seeker": "thewhiteh4t/seeker",
    "weaviate": "weaviate/weaviate",
    # web-platforms
    "jekyll": "jekyll/jekyll",
    "kramdown": "gettalong/kramdown",
    "huggingface_hub": "huggingface/huggingface_hub",
    "Telegram-iOS": "TelegramMessenger/Telegram-iOS",
    "goatcounter": "arp242/goatcounter",
}


def _resolve_url(name: str) -> str | None:
    """Resolve a repo name to a full clone URL.

    Handles three cases:
    1. name already contains "/" → use as-is (user-specified org/repo)
    2. name is in NAME_TO_REPO → use mapped org/repo
    3. unknown → fallback: try {name}/{name} pattern
    """
    # Already org/repo format
    if "/" in name:
        return f"https://github.com/{name}.git"

    mapped = NAME_TO_REPO.get(name)
    if mapped is not None:
        if not mapped:
            return None  # explicitly excluded (e.g. placeholder)
        return f"https://github.com/{mapped}.git"

    # Fallback: guess {lowercase_name}/{name}
    fallback = f"https://github.com/{name.lower()}/{name}.git"
    print(f"  [guess] {name} → {name.lower()}/{name}")
    return fallback


def clone_repo(category: str, name: str, dry_run: bool) -> tuple[str, bool, str]:
    """Clone a single repo into ~/projects/<name>/.

    Returns (name, success, message).
    """
    target = REPOS_BASE / name
    if target.exists():
        return name, True, "already exists"

    url = _resolve_url(name)
    if url is None:
        return name, False, "no mapping (ORG2 / placeholder)"

    if dry_run:
        return name, True, f"[DRY-RUN] would clone {url}"

    print(f"  cloning {name} ...", end="", flush=True)
    result = subprocess.run(
        ["git", "clone", "--depth", "10", url, str(target)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(" done")
        return name, True, f"cloned from {url}"
    else:
        err = result.stderr.strip().split("\n")[-1] if result.stderr else "unknown error"
        print(f" failed: {err}")
        # Clean up partial clone
        if target.exists():
            subprocess.run(["rm", "-rf", str(target)], capture_output=True)
        return name, False, err


def main():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        data = json.load(f)

    repos = data.get("repos", {})
    if not repos:
        print("No repos found in config.")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    category_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("@") and not arg.startswith("--"):
            category_filter = arg[1:]

    total = sum(len(v) for v in repos.values())
    print(f"Projects base: {REPOS_BASE}")
    print(f"Initializing {total} repos{' (dry run)' if dry_run else ''}...\n")

    results: list[tuple[str, str, bool, str]] = []  # (category, name, ok, msg)
    start = time.monotonic()

    for cat, entries in repos.items():
        if category_filter and cat != category_filter:
            continue
        print(f"[{cat}] ({len(entries)} repos)")
        for name in entries:
            ok, msg = clone_repo(cat, name, dry_run)[1:3]
            results.append((cat, name, ok, msg))
        print()

    elapsed = time.monotonic() - start
    ok_count = sum(1 for *_, ok, _ in results if ok)
    fail_count = sum(1 for *_, ok, _ in results if not ok)

    if fail_count:
        print("Failed repos:")
        for cat, name, ok, msg in results:
            if not ok:
                print(f"  [{cat}] {name}: {msg}")
        print()

    print(f"Done: {ok_count} ok, {fail_count} failed ({elapsed:.1f}s)")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())