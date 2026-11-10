"""
Télécharge le wheel précompilé de llama-cpp-python (CPU) adapté à la
plateforme courante dans vendor/wheels/, pour un embarquement dans le repo.

Usage (une fois, par le mainteneur, puis commit du fichier .whl) :
    python tools/fetch_local_wheel.py
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WHEELS_DIR = REPO_ROOT / "vendor" / "wheels"
CPU_INDEX = "https://abetlen.github.io/llama-cpp-python/whl/cpu"


def main() -> int:
    WHEELS_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(WHEELS_DIR.glob("llama_cpp_python-*.whl"))
    if existing:
        print(f"Wheel déjà embarqué : {existing[0].name}")
        return 0

    print(f"Téléchargement du wheel précompilé depuis {CPU_INDEX} ...")
    result = subprocess.run(
        [
            sys.executable, "-m", "pip", "download",
            "llama-cpp-python",
            "--no-deps",
            "--only-binary", ":all:",
            "--extra-index-url", CPU_INDEX,
            "-d", str(WHEELS_DIR),
        ],
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        print("Échec du téléchargement (pas de wheel pour cette plateforme ?).")
        return 1

    wheel = sorted(WHEELS_DIR.glob("llama_cpp_python-*.whl"))[0]
    print(f"Wheel embarqué : {wheel}")
    print("N'oubliez pas de le committer : git add vendor/wheels")
    return 0


if __name__ == "__main__":
    sys.exit(main())
