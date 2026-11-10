# Wheels embarquées du mode local

Ce dossier peut contenir le wheel précompilé de `llama-cpp-python` (CPU),
commité directement dans le repo. Au lancement en mode local, les scripts
(`launch.bat`, `launch.sh`, `src/bootstrap.py`) installent d'abord depuis ce
dossier (`--no-index --find-links vendor/wheels`) : **aucune compilation C,
aucun téléchargement** n'est alors nécessaire.

Pour embarquer le wheel (à faire une fois par le mainteneur, puis commit) :

```bash
python tools/fetch_local_wheel.py
```

Le script télécharge le wheel précompilé adapté à la plateforme courante depuis
l'index `cpu` officiel d'abetlen (ex. `llama_cpp_python-0.3.36-py3-none-win_amd64.whl`
sur Windows, compatible Python 3.13).

Notes :

- Taille : quelques dizaines de Mo. Un commit direct convient (limite GitHub :
  100 Mo/fichier) ; pour alléger l'historique, utiliser Git LFS sur `vendor/wheels/*.whl`.
- Sans wheel embarqué, les scripts retombent sur l'index en ligne
  `https://abetlen.github.io/llama-cpp-python/whl/cpu`.
- Le modèle GGUF (2 à 4,4 Go) ne tient pas dans git : il reste téléchargé au
  premier lancement via `download_model.py`, ou à placer manuellement dans `models/`.
