#!/bin/bash
# MonsterGen - Script de lancement pour Linux/macOS
# Ce script crée un environnement virtuel Python et lance l'application

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python n'est pas installé"
    echo "Veuillez installer Python 3.8 ou supérieur"
    exit 1
fi

# Créer un environnement virtuel si il n'existe pas
if [ ! -d "venv" ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances si nécessaire
if [ ! -d "venv/lib/python3.*/site-packages/PyQt6" ]; then
    echo "Installation des dépendances..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Installer les dépendances système pour PyQt6 (Linux)
if [ "$OSTYPE" = "linux-gnu" ] || [ "$OSTYPE" = "linux-musl" ]; then
    if ! ldd /usr/lib/libGL.so.1 &> /dev/null; then
        echo "Installation des dépendances système pour PyQt6..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y libgl1-mesa-glx
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y mesa-libGL
        elif command -v yum &> /dev/null; then
            sudo yum install -y mesa-libGL
        fi
    fi
fi

# Lancer l'application
echo "Lancement de MonsterGen..."
python main.py

# Désactiver l'environnement virtuel à la sortie
deactivate
