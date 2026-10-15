#!/bin/bash
# MonsterGen - Script de lancement pour Linux/macOS
# Utilise uv pour créer un environnement virtuel Python 3.13 (téléchargé
# automatiquement par uv, sans toucher au Python du système), puis lance
# l'application. Au démarrage, il propose : mode API (direct) ou tentative
# d'installation du modèle local (llama-cpp-python + téléchargement GGUF).

set -e

# Vérifier que uv est installé ; sinon l'installer automatiquement
if ! command -v uv &> /dev/null; then
    echo "uv n'est pas installé : installation automatique..."
    if command -v curl &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    else
        echo "Erreur : curl est requis pour installer uv."
        echo "Installez uv manuellement : https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    # uv s'installe dans ~/.local/bin : l'ajouter au PATH de la session
    export PATH="$HOME/.local/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "Erreur : uv n'a pas pu être installé."
        exit 1
    fi
fi

# Créer l'environnement virtuel Python 3.13 si nécessaire
# (uv télécharge l'interpréteur 3.13 lui-même, aucun Python 3.13 système requis)
if [ ! -d ".venv" ]; then
    echo "Création de l'environnement virtuel Python 3.13..."
    uv venv --python 3.13 .venv
fi

# Installer/synchroniser les dépendances dans l'environnement 3.13
echo "Installation des dépendances (Python 3.13)..."
uv pip install -r requirements.txt --python .venv

# Installer les dépendances système pour PySide6 (Linux)
if [ "$OSTYPE" = "linux-gnu" ] || [ "$OSTYPE" = "linux-musl" ]; then
    if ! ldd /usr/lib/libGL.so.1 &> /dev/null; then
        echo "Installation des dépendances système pour PySide6..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y libgl1-mesa-glx || sudo apt-get install -y libgl1
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y mesa-libGL
        elif command -v yum &> /dev/null; then
            sudo yum install -y mesa-libGL
        fi
    fi
fi

# Activer l'environnement virtuel Python 3.13
source .venv/bin/activate
PY=".venv/bin/python"

# Vérifier la version de Python de l'environnement (3.13 requis)
echo "Python utilisé : $($PY --version)"
PY_MINOR=$($PY -c "import sys; print(sys.version_info[1])")
PY_MAJOR=$($PY -c "import sys; print(sys.version_info.major)")
if [ "$PY_MAJOR" != "3" ] || [ "$PY_MINOR" != "13" ]; then
    echo ""
    echo "ERREUR : Python 3.13 est requis, mais l'environnement contient Python $PY_MAJOR.$PY_MINOR."
    echo "Supprimez le dossier .venv et relancez pour recréer un environnement Python 3.13 :"
    echo "  rm -rf .venv && ./launch.sh"
    exit 1
fi
echo "Version Python 3.13 vérifiée."

# Choix du mode IA
echo ""
echo "======================================"
echo "   MonsterGen - Mode de lancement"
echo "======================================"
echo "  1) Mode API (lancement direct)"
echo "     -> nécessite une clé API (Fichier > Configuration)"
echo "  2) Mode local (tentative d'installation du modèle)"
echo "     -> installe llama-cpp-python puis télécharge le modèle GGUF"
echo ""
read -rp "Votre choix [1/2] (défaut : 1) : " choice

set_ai_mode() {
    $PY -c "from config.config_manager import config_manager; config_manager.set_ai_mode('$1')"
}

case "$choice" in
    2)
        echo "Tentative d'installation du modèle local..."
        if $PY -c "import llama_cpp" 2>/dev/null; then
            echo "llama-cpp-python est déjà installé."
        else
            echo "Installation de llama-cpp-python (wheel précompilée d'abord)…"
            if ! uv pip install llama-cpp-python \
                --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/stable \
                --python .venv; then
                echo ""
                echo "Échec de l'installation de llama-cpp-python."
                echo "Retour en mode API."
                set_ai_mode "api"
            fi
        fi
        if $PY -c "import llama_cpp" 2>/dev/null; then
            echo "Vérification/téléchargement du modèle GGUF..."
            $PY download_model.py || set_ai_mode "api"
        fi
        ;;
    *)
        echo "Lancement en mode API..."
        set_ai_mode "api"
        ;;
esac

# Lancer l'application
echo ""
echo "Lancement de MonsterGen..."
$PY main.py

# Désactiver l'environnement virtuel à la sortie
deactivate
