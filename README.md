# MonsterGen - Générateur de fiches DnD 5e

📖 **Documentation complète : [docs/Home.md](docs/Home.md)** — installation, utilisation, architecture, règles de génération, backends IA, exports.

MonsterGen est une application Python qui génère des fiches de PNJ, monstres et ennemis pour Donjons & Dragons 5e, avec statistiques équilibrées selon les tables officielles et génération de texte par IA locale ou API.

## Fonctionnalités

### Génération de statistiques (tables officielles, sans IA)
- **Stats équilibrées par groupe** : nombre de joueurs, niveau moyen et difficulté (Facile/Moyen/Difficile/Mortel) déterminent le CR cible via les seuils de PX du Guide du Maître — label coloré en temps réel
- **CR en fractions** (1/8, 1/4, 1/2, 1 à 30) avec points d'expérience
- **Tout le bloc de stats** : CA, PV + dés de vie cohérents, vitesse, caractéristiques, actions d'attaque chiffrées (bonus au toucher, dégâts, DD de sauvegarde)
- **Inférence de traits** : la race et la description rendent les stats crédibles — archétype (brute, mage, discret…), armes cohérentes, type de dégâts de l'action spéciale, vitesse (vol/nage/fouisse), compétences maîtrisées, résistances et immunités
- **Aucune valeur saisie n'est écrasée** : la génération ne complète que les champs vides

### IA (au choix)
- **Modèle local** (défaut) : petit modèle GGUF exécuté en locale via llama-cpp-python (Qwen2.5-3B ~2 Go ou Mistral-7B ~4,4 Go) — hors ligne, aucune clé API
- **API distante** : compatible OpenAI/Mistral (clé + endpoint), idéal pour machine peu puissante
- **Généré par l'IA** : noms, races, descriptions, actions de combat complètes (avec correction automatique des stats manquantes), scénarios de rencontre de combat (contexte, **tactique du monstre**, ciblage, repli), correction orthographique de tous les champs remplis

### Interface
- **Trois onglets** : Informations de base, Statistiques, Actions et Équipement
- **Champs en « pills »** : langues, compétences maîtrisées, résistances, immunités (suggestions DnD 5e, croix pour retirer)
- **Cartes d'action éditables** : nom + description contenant toutes les stats de combat, suppression par croix
- **Bibliothèque** : menu dédié listant les sauvegardes (sauvegarder avec nom éditable, charger, supprimer)
- **Étiquette de statut** : mode IA actif affiché en permanence en haut de l'UI

### Exports
- **PNG au style du stat block officiel** : fond parchemin, titres rouge brique, scénario formaté (sous-titres en gras)
- **PDF** : fiche complète classique
- **JSON** : format de sauvegarde de la bibliothèque

## Installation

### Prérequis

- Python 3.10+ recommandé (3.8 minimum)
- ~2 à 5 Go d'espace disque pour le modèle IA local (optionnel)

### Lancer

```bash
git clone https://github.com/GuillaumeRoeder/MonsterGen
cd MonsterGen
python main.py
```

**Aucune installation manuelle** : au premier lancement, l'application vérifie et installe automatiquement ses dépendances, y compris `llama-cpp-python` (wheel précompilé priorisé). Si ce dernier échoue, l'UI démarre quand même avec un popup et bascule en mode API.

### Modèle IA local (optionnel)

```bash
python download_model.py        # Qwen2.5-3B (~2 Go), défaut
python download_model.py 4gb    # Mistral-7B (~4,4 Go), meilleurs textes en français
```

Ou laissez l'application le proposer au premier clic de génération.

### Mode API (aucun modèle requis)

**Fichier > Configuration > Mode IA : API distante** — renseignez une clé (gratuite sur console.mistral.ai), modèle `mistral-small-latest`, endpoint par défaut.

### Dépendances système (Linux)

```bash
# Debian/Ubuntu
sudo apt-get install libgl1-mesa-glx

# Fedora/RHEL
sudo dnf install mesa-libGL
```

## Utilisation

1. **Configurez le groupe** (tab Statistiques) : joueurs, niveau moyen, difficulté — le CR résultant s'affiche en temps réel
2. **Saisissez le concept** : nom, race, description, langues (tout optionnel — mais plus il y a de contexte, plus les stats sont crédibles)
3. **« Générer les champs manquants »** : correction orthographique des champs remplis, génération IA des champs vides, équilibrage complet des stats, actions régénérées selon le contexte
4. **« Générer scénario »** : rencontre de combat avec la tactique du monstre face au groupe
5. **Exportez** : PNG (style officiel), PDF, ou sauvegardez dans la **Bibliothèque**

## Configuration

Via **Fichier > Configuration**, persistée dans `config/config.json` :

```json
{
    "ai_mode": "local",
    "local_model_size": "2gb",
    "local_model_path": "",
    "local_context": 4096,
    "local_threads": 4,
    "api_key": "",
    "api_endpoint": "https://api.mistral.ai/v1/chat/completions",
    "api_model": "mistral-small-latest",
    "default_save_path": "./fiches",
    "language": "fr"
}
```

## Structure du projet

```
MonsterGen/
├── main.py                  # Point d'entrée : bootstrap, menus
├── download_model.py        # Téléchargement du modèle GGUF
├── config/
│   └── config_manager.py    # Configuration persistée
├── src/
│   ├── bootstrap.py         # Auto-installation des dépendances
│   ├── models/
│   │   └── monster.py       # Dataclass Monster + sérialisation
│   ├── rules/               # Moteur DnD 5e (aucune IA)
│   │   ├── stat_builder.py  # Tables DMG : CA, PV, actions
│   │   ├── encounter.py     # Budget de PX, CR selon le groupe
│   │   └── trait_inference.py  # Race/description → archétype, armes…
│   ├── ai/
│   │   ├── ai_generator.py  # Prompts + parsing
│   │   ├── local_model.py   # Client GGUF (llama-cpp-python)
│   │   └── api_client.py    # Client API distante
│   ├── ui/
│   │   ├── main_window.py   # Fenêtre principale
│   │   ├── config_dialog.py
│   │   ├── monster_library.py  # Gestionnaire de sauvegardes
│   │   ├── action_editor.py    # Cartes d'action
│   │   └── pill_editor.py      # Éditeurs en pills
│   └── export/
│       ├── png_exporter.py  # Fiche style stat block officiel
│       └── pdf_exporter.py
├── docs/                    # Documentation détaillée
└── requirements.txt
```

## Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou une pull request sur GitHub.

## Licence

MIT License

## Auteur

Guillaume Roeder
