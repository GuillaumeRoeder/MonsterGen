# MonsterGen - Générateur de fiches DnD 5e

📖 **Documentation complète : [docs/Home.md](docs/Home.md)** — installation, utilisation, architecture, règles de génération, backends IA, exports.

MonsterGen est une application Python qui permet de générer des fiches PDF pour les PNJ, monstres et ennemis de Donjons & Dragons 5e.

## Fonctionnalités

- **Interface graphique** : UI complète avec des champs à remplir optionnellement
- **Modèle IA local** : Génération des descriptions, actions et scénarios via un petit modèle embarqué (GGUF, 2 à 6 Go) exécuté en locale — aucune clé API nécessaire
- **Stats équilibrées** : Remplissage direct des statistiques (CA, PV, dés de vie, caractéristiques, actions) à partir des tables officielles du Guide du Maître, en fonction du niveau de difficulté (CR)
- **Niveau de difficulté** : Panel hardcodé de CR affichés en fraction (1/8, 1/4, 1/2, 1, 2…)
- **Scénario de rencontre** : Généré via un bouton dédié, basé sur les stats actuelles du monstre
- **Export PDF** : Génération de fiches PDF professionnelles
- **Multiplateforme** : Fonctionne sur Linux et Windows
- **Sauvegarde/Chargement** : Sauvegarder et charger vos créations

## Champs pris en charge

### Informations de base
- Nom
- Race
- Description
- Alignement (Loyal Bon, Neutre, Chaotique Mauvais, etc.)
- Taille (Minuscule, Petit, Moyen, Grand, Énorme, Gigantesque)

### Statistiques
- Classe d'Armure (CA)
- Points de Vie (PV)
- Dés de Vie
- Vitesse
- Caractéristiques (FOR, DEX, CON, INT, SAG, CHA)
- Challenge Rating (CR)

### Défense
- Résistances aux dégâts
- Immunités aux dégâts
- Vulnérabilités aux dégâts
- Immunités aux états

### Sens et Langues
- Sens spéciaux
- Perception passive
- Langues parlées

### Actions
- Actions normales
- Actions légendaires
- Réactions

### Autres
- Trésor
- Notes

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip

### Installation des dépendances

Rien à faire manuellement : au premier lancement (`python main.py` ou
`python download_model.py`), l'application vérifie et installe
automatiquement toutes les dépendances manquantes, y compris
`llama-cpp-python` (wheel précompilé priorisé, pas besoin de compilateur C).

Installation manuelle si vous préférez :

```bash
pip install -r requirements.txt
```

### Dépendances système (Linux)

Pour PyQt6, vous aurez besoin de :

```bash
# Debian/Ubuntu
sudo apt-get install libgl1-mesa-glx

# Fedora/RHEL
sudo dnf install mesa-libGL
```

## Configuration

Deux modes IA au choix (menu "Fichier > Configuration") :

1. **Modèle local** (défaut) : modèle GGUF embarqué (2 Go ou 4,4 Go), fonctionne hors ligne, aucune clé API. Téléchargez-le avec `python download_model.py` (ou automatiquement depuis l'application)
2. **API distante** : renseignez clé API, modèle et endpoint (compatible OpenAI/Mistral — défaut : Mistral AI). Utile si votre machine est peu puissante

La configuration se fait via le menu "Fichier > Configuration" dans l'application.

## Utilisation

1. Lancez l'application :
   ```bash
   python main.py
   ```

2. Remplissez les champs que vous connaissez

3. Cliquez sur "Générer les champs manquants" pour que l'IA complète les informations manquantes

4. Sélectionnez les options proposées ou modifiez-les

5. Exportez en PDF via le bouton "Exporter en PDF"

## Exemple de fichier de configuration

Le fichier de configuration est stocké dans `config/config.json` :

```json
{
    "ai_api_key": "votre_clé_api",
    "ai_model": "mistral-tiny",
    "ai_endpoint": "https://api.mistral.ai/v1/chat/completions",
    "default_save_path": "./fiches",
    "language": "fr"
}
```

## Structure du projet

```
MonsterGen/
├── config/
│   ├── __init__.py
│   └── config_manager.py
├── src/
│   ├── __init__.py
│   ├── ai/
│   │   ├── __init__.py
│   │   └── ai_generator.py
│   ├── export/
│   │   ├── __init__.py
│   │   └── pdf_exporter.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── monster.py
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py
│       └── config_dialog.py
├── main.py
├── requirements.txt
└── README.md
```

## Contribution

Les contributions sont les bienvenues ! Ouvrez une issue ou une pull request sur GitHub.

## Licence

MIT License

## Auteur

Guillaume Roeder
