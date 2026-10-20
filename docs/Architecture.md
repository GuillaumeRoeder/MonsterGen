# Architecture

```
MonsterGen/
├── main.py                  # Point d'entrée : bootstrap, menus, fenêtre
├── download_model.py        # Téléchargement du modèle GGUF (une fois)
├── config/
│   └── config_manager.py    # Configuration persistée (config/config.json)
├── src/
│   ├── bootstrap.py         # Auto-installation des dépendances
│   ├── models/
│   │   └── monster.py       # Dataclass Monster + Action, (dé)sérialisation
│   ├── rules/               # Moteur de règles DnD 5e (aucune IA)
│   │   ├── stat_builder.py  # Tables DMG : CA, PV, dés de vie, actions
│   │   ├── encounter.py     # Budget de PX, CR selon groupe/difficulté
│   │   └── trait_inference.py  # Race/description -> archétype, armes, etc.
│   ├── ai/
│   │   ├── ai_generator.py  # Prompts + parsing (textes, actions, scénario)
│   │   ├── local_model.py   # Client GGUF via llama-cpp-python
│   │   └── api_client.py    # Client API distante (OpenAI/Mistral)
│   ├── ui/
│   │   ├── main_window.py   # Fenêtre principale, tabs, orchestration
│   │   ├── config_dialog.py # Configuration
│   │   ├── monster_library.py  # Popup bibliothèque de sauvegardes
│   │   ├── action_editor.py    # Carte d'action éditable
│   │   ├── pill_editor.py      # Éditeur en pills générique
│   │   └── languages_editor.py
│   └── export/
│       ├── png_exporter.py  # Fiche PNG style stat block officiel
│       └── pdf_exporter.py  # Export PDF
└── docs/                    # Ce wiki
```

## Principes clés

### Séparation règles / IA
Les **statistiques chiffrées** ne passent jamais par l'IA : `src/rules/` les calcule à partir des tables du DMG — reproductible, instantané, sans hallucination. L'IA (locale ou API) ne gère que le **texte** : noms, descriptions, actions détaillées, scénarios.

### Routage des backends
Toute génération passe par `_backend_generate()` (`ai_generator.py`) qui consulte la configuration : mode `local` → `local_model` (GGUF), mode `api` → `api_client`. Les prompts sont identiques dans les deux cas.

### Bootstrap non bloquant
`src/bootstrap.py` installe les dépendances au lancement. `llama-cpp-python` est optionnel : en cas d'échec, la config bascule en mode API et un popup prévient — l'UI démarre toujours.

### Widgets composites
Les actions, langues, compétences et résistances utilisent des widgets riches (cartes éditable, pills détachables) plutôt que des champs texte plats — les valeurs structurées restent lisibles et manipulables.
