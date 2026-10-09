@echo off
:: MonsterGen - Script de lancement pour Windows
:: Ce script crée un environnement virtuel Python et lance l'application

:: Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur: Python n'est pas installé ou n'est pas dans le PATH
    echo Veuillez installer Python 3.8 ou supérieur depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Créer un environnement virtuel si il n'existe pas
if not exist "venv\" (
    echo Création de l'environnement virtuel...
    python -m venv venv
)

:: Activer l'environnement virtuel
call venv\Scripts\activate.bat

:: Installer les dépendances si nécessaire
if not exist "venv\Lib\site-packages\PyQt6" (
    echo Installation des dépendances...
    pip install --upgrade pip
    pip install -r requirements.txt
)

:: Lancer l'application
python main.py

:: Désactiver l'environnement virtuel à la sortie
call venv\Scripts\deactivate.bat
