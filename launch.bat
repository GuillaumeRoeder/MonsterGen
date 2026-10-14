@echo off
:: MonsterGen - Script de lancement pour Windows
:: Ce script crée un environnement virtuel Python et lance l'application.
:: Au démarrage, il propose : mode API (direct) ou tentative d'installation
:: du modèle local (llama-cpp-python + téléchargement GGUF).

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

:: Choix du mode IA
echo.
echo ======================================
echo    MonsterGen - Mode de lancement
echo ======================================
echo   1) Mode API (lancement direct)
echo      -^> necessite une cle API (Fichier ^> Configuration)
echo   2) Mode local (tentative d'installation du modele)
echo      -^> installe llama-cpp-python puis telecharge le modele GGUF
echo.
set /p choice="Votre choix [1/2] (defaut : 1) : "

if "%choice%"=="2" goto local_mode
goto api_mode

:local_mode
echo Tentative d'installation du modele local...
python -c "import llama_cpp" >nul 2>&1
if not errorlevel 1 (
    echo llama-cpp-python est deja installe.
    goto download_model
)
pip install llama-cpp-python
if errorlevel 1 (
    echo.
    echo Echec de l'installation de llama-cpp-python.
    echo Retour en mode API.
    python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"
    goto launch
)

:download_model
echo Verification/telechargement du modele GGUF...
python download_model.py
if errorlevel 1 (
    echo Echec du telechargement du modele. Retour en mode API.
    python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"
)
goto launch

:api_mode
echo Lancement en mode API...
python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"

:launch
:: Lancer l'application
echo.
echo Lancement de MonsterGen...
python main.py

:: Désactiver l'environnement virtuel à la sortie
call venv\Scripts\deactivate.bat
