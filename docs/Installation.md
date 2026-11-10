# Installation

## Prérequis

- **Python 3.10+** recommandé (3.8 minimum mais certains paquets récents l'abandonnent)
- ~2 à 5 Go d'espace disque pour le modèle IA local (optionnel)
- Connexion internet au premier lancement (installation auto + téléchargement du modèle)

## Installation

```bash
git clone https://github.com/GuillaumeRoeder/MonsterGen
cd MonsterGen
python main.py
```

C'est tout : **l'application installe elle-même ses dépendances** au premier lancement (`src/bootstrap.py`), y compris `llama-cpp-python` (wheel précompilé priorisé, pas besoin de compilateur C). Si ce dernier échoue, l'UI démarre quand même avec un popup et bascule en mode API.

## Mode local embarqué (hors ligne dès le clone)

Le repo peut embarquer directement le wheel précompilé CPU de `llama-cpp-python`
dans `vendor/wheels/` : au lancement en mode local (`launch.bat` / `launch.sh` /
`bootstrap.py`), l'installation se fait alors **sans téléchargement ni compilation**.

Pour (ré)embarquer le wheel adapté à votre plateforme :

```bash
python tools/fetch_local_wheel.py   # télécharge dans vendor/wheels/
git add vendor/wheels               # à committer une fois
```

Sans wheel embarqué, les scripts retombent automatiquement sur l'index en ligne
`https://abetlen.github.io/llama-cpp-python/whl/cpu` (wheel `py3-none-win_amd64`
disponible, compatible Python 3.13). Le modèle GGUF (2 à 4,4 Go) reste téléchargé
au premier lancement ou à placer manuellement dans `models/` — trop volumineux pour git.

## Modèle IA local (optionnel, recommandé)

Pour la génération hors ligne sans clé API :

```bash
python download_model.py        # modèle par défaut (~2 Go, Qwen2.5-3B)
python download_model.py 4gb   # variante plus performante (~4,4 Go, Mistral-7B)
```

Le fichier `.gguf` arrive dans `models/` à la racine. Alternative : laisser l'application le télécharger au premier clic sur un bouton de génération.

## Mode API (aucun modèle requis)

**Configuration > Mode IA : API distante**, renseignez une clé (gratuite sur console.mistral.ai), modèle `mistral-small-latest`, endpoint par défaut. Voir [Backends IA](Backends-IA.md).

## Dépannage

| Symptôme | Solution |
|---|---|
| `can't open file 'main.py'` | Lancez depuis la racine du repo |
| Échec d'installation de llama-cpp-python | Mode API, ou embarquer le wheel via `python tools/fetch_local_wheel.py` (pas besoin des Build Tools C++) |
| `libGL` manquant (Linux) | `sudo apt install libgl1` |
| UI figée pendant une génération | Normal avec le modèle local — attendez quelques secondes |

## Branche de développement

Les dernières fonctionnalités sont sur la branche `vibe/local-model-balanced-stats-fd4f7c` (PR #1) jusqu'à fusion :

```bash
git checkout vibe/local-model-balanced-stats-fd4f7c
```
