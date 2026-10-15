@echo off
:: MonsterGen - Script de lancement pour Windows
:: Utilise uv pour créer un environnement virtuel Python 3.13 (téléchargé
:: automatiquement par uv, sans toucher au Python du système), puis lance
:: l'application. Au démarrage, il propose : mode API (direct) ou tentative
:: d'installation du modèle local (llama-cpp-python + téléchargement GGUF).

:: Vérifier que uv est installé ; sinon l'installer automatiquement
where uv >nul 2>&1
if errorlevel 1 (
    echo uv n'est pas installe : installation automatique...
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo Erreur : uv n'a pas pu etre installe.
        echo Installez uv manuellement : https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    set "PATH=%USERPROFILE%\.local\bin;%PATH%"
)

:: Créer l'environnement virtuel Python 3.13 si nécessaire
:: (uv télécharge l'interpréteur 3.13 lui-même, aucun Python 3.13 système requis)
if not exist ".venv\" (
    echo Creation de l'environnement virtuel Python 3.13...
    uv venv --python 3.13 .venv
    if errorlevel 1 (
        echo Erreur : impossible de creer l'environnement Python 3.13.
        pause
        exit /b 1
    )
)

:: Installer/synchroniser les dépendances dans l'environnement 3.13
echo Installation des dependances ^(Python 3.13^)...
uv pip install -r requirements.txt --python .venv
if errorlevel 1 (
    echo Erreur : echec de l'installation des dependances.
    pause
    exit /b 1
)

:: Activer l'environnement virtuel Python 3.13
call .venv\Scripts\activate.bat

:: Vérifier la version de Python de l'environnement (3.13 requis)
echo Python utilise :
.venv\Scripts\python --version
.venv\Scripts\python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 13) else 1)"
if errorlevel 1 (
    echo.
    echo ERREUR : Python 3.13 est requis.
    echo Supprimez le dossier .venv et relancez pour recreer un environnement Python 3.13.
    pause
    exit /b 1
)
echo Version Python 3.13 verifiee.

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
.venv\Scripts\python -c "import llama_cpp" >nul 2>&1
if not errorlevel 1 (
    echo llama-cpp-python est deja installe.
    goto download_model
)
uv pip install llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/stable --python .venv
if errorlevel 1 (
    echo.
    echo Echec de l'installation de llama-cpp-python.
    echo Retour en mode API.
    .venv\Scripts\python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"
    goto launch
)

:download_model
echo Verification/telechargement du modele GGUF...
.venv\Scripts\python download_model.py
if errorlevel 1 (
    echo Echec du telechargement du modele. Retour en mode API.
    .venv\Scripts\python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"
)
goto launch

:api_mode
echo Lancement en mode API...
.venv\Scripts\python -c "from config.config_manager import config_manager; config_manager.set_ai_mode('api')"

:launch
:: Lancer l'application
echo.
echo Lancement de MonsterGen...
.venv\Scripts\python main.py

:: Désactiver l'environnement virtuel à la sortie
call .venv\Scripts\deactivate.bat
