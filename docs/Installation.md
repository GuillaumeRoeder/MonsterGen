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

## Modèle IA local (optionnel, recommandé)

Pour la génération hors ligne sans clé API :

```bash
python download_model.py        # modèle par défaut (~2 Go, Qwen2.5-3B)
python download_model.py 4gb   # variante plus performante (~4,4 Go, Mistral-7B)
```

Le fichier `.gguf` arrive dans `models/` à la racine. Alternative : laisser l'application le télécharger au premier clic sur un bouton de génération.

## Mode API (aucun modèle requis)

**Fichier > Configuration > Mode IA : API distante**, renseignez une clé (gratuite sur console.mistral.ai), modèle `mistral-small-latest`, endpoint par défaut. Voir [Backends IA](Backends-IA.md).

## Dépannage

| Symptôme | Solution |
|---|---|
| `can't open file 'main.py'` | Lancez depuis la racine du repo |
| Échec d'installation de llama-cpp-python | Basculer en mode API, ou installer les Build Tools C++ |
| `libGL` manquant (Linux) | `sudo apt install libgl1` |
| UI figée pendant une génération | Normal avec le modèle local — attendez quelques secondes |

## Branche de développement

Les dernières fonctionnalités sont sur la branche `vibe/local-model-balanced-stats-fd4f7c` (PR #1) jusqu'à fusion :

```bash
git checkout vibe/local-model-balanced-stats-fd4f7c
```
