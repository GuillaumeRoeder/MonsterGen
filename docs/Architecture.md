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
│   ├── core/                # Systèmes métier (sans UI)
│   │   └── monster_manager.py  # Monstre courant + exports PNG/PDF
│   ├── library/             # Système bibliothèque (sans UI)
│   │   ├── library_manager.py  # Sauvegardes : liste/load/save/delete/import/export
│   │   └── encounter_manager.py  # Sauvegardes de rencontres
│   ├── rules/               # Moteur de règles DnD 5e (aucune IA)
│   │   ├── stat_builder.py  # Tables DMG : CA, PV, dés de vie, actions
│   │   ├── encounter.py     # Budget de PX, CR selon groupe/difficulté
│   │   ├── encounter_builder.py  # Rencontres multi-monstres : multiplicateurs, quantités
│   │   └── trait_inference.py  # Race/description -> archétype, armes, etc.
│   ├── ai/
│   │   ├── ai_generator.py  # Prompts + parsing (textes, actions, scénario)
│   │   ├── local_model.py   # Client GGUF via llama-cpp-python
│   │   └── api_client.py    # Client API distante (OpenAI/Mistral)
│   ├── ui/
│   │   ├── main_window.py   # Orchestrateur : assemble les widgets, génération
│   │   ├── config_dialog.py # Configuration
│   │   ├── monster_library.py  # Dialogues bibliothèque (appelle LibraryManager)
│   │   ├── encounter_tab.py    # Onglet Rencontre : sélection, quantités, scénario
│   │   ├── dnd_data.py     # Listes de référence DnD 5e (races, skills, dégâts)
│   │   ├── action_editor.py    # Carte d'action éditable
│   │   ├── pill_editor.py      # Éditeur en pills générique
│   │   ├── languages_editor.py
│   │   └── widgets/         # Compartiments de l'UI, appelés par MainWindow
│   │       ├── basic_tab.py        # Onglet Description (identité, scénario)
│   │       ├── stats_tab.py        # Onglet Statistiques
│   │       ├── actions_tab.py      # Onglet Actions
│   │       ├── equipment_widget.py # Section Équipement repliable
│   │       ├── preview_panel.py    # Aperçu de la fiche (moitié droite)
│   │       ├── party_widget.py     # Groupe joueurs + difficulté
│   │       ├── card_list.py        # Liste scrollable de cartes (générique)
│   │       └── collapsible_header.py  # Barre de titre repliable
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

### Compartimentation UI / systèmes
Chaque système est une classe à part, appelée par l'UI :
- **`MonsterManager`** (`src/core/`) détient le monstre courant et délègue les exports PNG/PDF ; l'UI ne touche jamais les exporteurs directement.
- **`LibraryManager`** (`src/library/`) concentre toute la persistance des sauvegardes (liste, chargement, écriture, suppression, import/export de fichiers) ; les dialogues de `monster_library.py` ne sont que des coquilles Qt.
- **Un widget par compartiment d'UI** (`src/ui/widgets/`) : chaque onglet et le panneau d'aperçu sont des classes autonomes avec leurs signaux ; `MainWindow` se réduit à un orchestrateur (assemblage, conversion formulaire ↔ `Monster`, orchestration règles + IA).
- Les widgets génériques (`card_list.py`, `collapsible_header.py`, `party_widget.py`) sont réutilisés par plusieurs onglets.
