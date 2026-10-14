"""
Module de modèle IA local pour MonsterGen.

Utilise un petit modèle GGUF (2 à 6 Go) exécuté en locale via
llama-cpp-python — aucune clé API ni service distant n'est nécessaire.
Le modèle est téléchargé une seule fois par le script download_model.py
(ou automatiquement au premier lancement si huggingface_hub est disponible).
"""

import threading
from pathlib import Path
from typing import Optional

from config.config_manager import config_manager

# Panel hardcodé des modèles locaux embarquables (<= 6 Go).
LOCAL_MODELS = {
    "2gb": {
        "label": "Qwen2.5 3B Instruct Q4_K_M (~2 Go)",
        "repo_id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "default_path": "models/qwen2.5-3b-instruct-q4_k_m.gguf",
        "ctx": 4096,
    },
    "4gb": {
        "label": "Mistral 7B Instruct v0.3 Q4_K_M (~4,4 Go)",
        "repo_id": "MaziyarJaber/Mistral-7B-Instruct-v0.3-GGUF",
        "filename": "Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
        "default_path": "models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf",
        "ctx": 4096,
    },
}
DEFAULT_MODEL_SIZE = "2gb"
MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "models"


class ModelNotAvailableError(RuntimeError):
    """Le modèle local n'est pas installé ou llama-cpp-python est absent."""


class LocalModelClient:
    """Client pour un modèle LLM local (GGUF via llama-cpp-python)."""

    def __init__(self):
        self._llm = None
        self._loaded_path: Optional[str] = None
        self._lock = threading.Lock()

    def get_model_info(self) -> dict:
        """Retourne la description du modèle sélectionné dans la config."""
        size = config_manager.get_local_model_size()
        return LOCAL_MODELS.get(size, LOCAL_MODELS[DEFAULT_MODEL_SIZE])

    def get_model_path(self) -> Path:
        """Chemin du fichier modèle (config ou emplacement par défaut)."""
        configured = config_manager.get_local_model_path()
        if configured and Path(configured).exists():
            return Path(configured)
        info = self.get_model_info()
        return Path(configured) if configured else MODELS_DIR / info["filename"]

    def is_available(self) -> bool:
        """Le modèle est-il téléchargé et llama-cpp-python installé ?"""
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            return False
        return self.get_model_path().exists()

    def download(self, progress_callback=None) -> Path:
        """Télécharge le modèle GGUF sélectionné depuis Hugging Face."""
        info = self.get_model_info()
        target = MODELS_DIR / info["filename"]
        if target.exists():
            return target

        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            from huggingface_hub import hf_hub_download
            downloaded = hf_hub_download(
                repo_id=info["repo_id"],
                filename=info["filename"],
                local_dir=str(MODELS_DIR),
            )
            return Path(downloaded)
        except ImportError:
            raise ModelNotAvailableError(
                "huggingface_hub n'est pas installé. "
                "Lancez : pip install huggingface_hub"
            )
        except Exception as e:
            raise ModelNotAvailableError(f"Échec du téléchargement du modèle : {e}")

    def _load(self):
        """Charge le modèle en mémoire (une seule fois)."""
        with self._lock:
            path = self.get_model_path()
            if self._llm is not None and self._loaded_path == str(path):
                return self._llm

            if not path.exists():
                raise ModelNotAvailableError(
                    f"Modèle introuvable : {path}\n"
                    "Lancez le script download_model.py pour le télécharger "
                    f"({self.get_model_info()['label']})."
                )

            try:
                from llama_cpp import Llama
            except ImportError:
                raise ModelNotAvailableError(
                    "llama-cpp-python n'est pas installé. "
                    "Lancez : pip install llama-cpp-python"
                )

            info = self.get_model_info()
            n_ctx = config_manager.get_local_context() or info["ctx"]
            n_threads = config_manager.get_local_threads() or 4

            self._llm = Llama(
                model_path=str(path),
                n_ctx=n_ctx,
                n_threads=n_threads,
                verbose=False,
            )
            self._loaded_path = str(path)
            return self._llm

    def generate(self, prompt: str, max_tokens: int = 400,
                 temperature: float = 0.7,
                 system_prompt: Optional[str] = None) -> str:
        """Génère du texte avec le modèle local."""
        llm = self._load()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            result = llm.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return result["choices"][0]["message"]["content"].strip()
        except ModelNotAvailableError:
            raise
        except Exception as e:
            raise ModelNotAvailableError(f"Erreur du modèle local : {e}")


# Instance globale
local_model = LocalModelClient()
