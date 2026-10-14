"""
Vérification et installation automatique des dépendances de MonsterGen.

Appelé au tout début de main.py : installe tout ce qui manque via pip
(en utilisant l'interpréteur courant), sans que l'utilisateur ait à lancer
de commandes manuellement. llama-cpp-python est d'abord installé depuis
l'index de wheels précompilés pour éviter d'avoir besoin d'un compilateur C.
"""

import importlib.util
import subprocess
import sys
from typing import List, Optional, Tuple

# (nom du module importable, spécification pip)
DEPENDENCIES: List[Tuple[str, str]] = [
    ("PySide6", "PySide6>=6.5.0"),
    ("requests", "requests>=2.31.0"),
    ("reportlab", "reportlab>=4.0.4"),
    ("dotenv", "python-dotenv>=1.0.0"),
    ("huggingface_hub", "huggingface_hub>=0.23.0"),
    ("tqdm", "tqdm>=4.66.0"),
    ("hf_transfer", "hf-transfer>=0.1.6"),
]

LLAMA_CPP_MODULE = "llama_cpp"
LLAMA_CPP_SPEC = "llama-cpp-python>=0.2.60"
LLAMA_CPP_WHEEL_INDEX = "https://abetlen.github.io/llama-cpp-python/whl/stable"


def _log(message: str):
    print(f"[MonsterGen] {message}", flush=True)


def _is_installed(module_name: str) -> bool:
    """Le module Python est-il déjà installé ?"""
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def _pip_install(spec: str, extra_args: Optional[List[str]] = None) -> bool:
    """Installe un paquet avec l'interpréteur courant. Retourne True si OK."""
    command = [sys.executable, "-m", "pip", "install", spec]
    if extra_args:
        command.extend(extra_args)
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.returncode == 0
    except OSError:
        return False


def install_llama_cpp() -> bool:
    """Installe llama-cpp-python : wheel précompilé d'abord, compilation ensuite."""
    if _is_installed(LLAMA_CPP_MODULE):
        return True

    _log("Installation de llama-cpp-python (wheel précompilé)…")
    if _pip_install(LLAMA_CPP_SPEC, [
        "--extra-index-url", LLAMA_CPP_WHEEL_INDEX,
        "--prefer-binary",
    ]):
        return True

    _log("Wheel précompilé indisponible, tentative par compilation (un compilateur C peut être requis)…")
    return _pip_install(LLAMA_CPP_SPEC)


def ensure_dependencies() -> None:
    """Vérifie et installe toutes les dépendances manquantes."""
    missing = [(module, spec) for module, spec in DEPENDENCIES
               if not _is_installed(module)]
    for module, spec in missing:
        _log(f"Installation de {spec}…")
        if not _pip_install(spec):
            raise RuntimeError(
                f"Impossible d'installer {spec} automatiquement.\n"
                f"Lancez manuellement : {sys.executable} -m pip install {spec}"
            )

    if not install_llama_cpp():
        raise RuntimeError(
            "Impossible d'installer llama-cpp-python automatiquement.\n"
            "Solutions :\n"
            f"  1. {sys.executable} -m pip install llama-cpp-python "
            f"--extra-index-url {LLAMA_CPP_WHEEL_INDEX}\n"
            f"  2. Ou lancez : {sys.executable} -m pip install llama-cpp-python "
            "(nécessite un compilateur C : Visual Studio Build Tools sous Windows)"
        )

    if missing:
        _log("Dépendances installées avec succès.")
