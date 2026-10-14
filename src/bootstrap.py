"""
Vérification et installation automatique des dépendances de MonsterGen.

Appelé au démarrage : installe ce qui manque via pip. Rien n'est bloquant
pour le démarrage de l'UI — si llama-cpp-python ne peut pas être installé
(compilation C impossible), l'application démarre quand même et bascule
en mode API. Seul PySide6 est indispensable.
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


class BootstrapError(RuntimeError):
    """Une dépendance indispensable n'a pas pu être installée."""


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
    """Installe les dépendances indispensables ; lève BootstrapError sinon."""
    for module, spec in DEPENDENCIES:
        if _is_installed(module):
            continue
        _log(f"Installation de {spec}…")
        if not _pip_install(spec):
            raise BootstrapError(
                f"Impossible d'installer {spec} automatiquement.\n"
                f"Lancez manuellement : {sys.executable} -m pip install {spec}"
            )


def ensure_optional_llama_cpp() -> bool:
    """Tente d'installer llama-cpp-python ; ne bloque jamais le démarrage."""
    return install_llama_cpp()


def llama_cpp_available() -> bool:
    """llama-cpp-python est-il importable ?"""
    return _is_installed(LLAMA_CPP_MODULE)
