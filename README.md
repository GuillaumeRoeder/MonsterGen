# MonsterGen - Générateur de fiches DnD 5e

MonsterGen est une application Python qui permet de générer des fiches PDF pour les PNJ, monstres et ennemis de Donjons & Dragons 5e.

## Fonctionnalités

- **Interface graphique** : UI complète avec des champs à remplir optionnellement
- **Génération IA** : Complétion automatique des champs manquants via une API IA (clé à fournir)
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

1. **Clé API IA** : Vous devez fournir une clé API pour un service d'IA compatible (Mistral AI, OpenAI, etc.)
2. **Modèle IA** : Sélectionnez le modèle à utiliser
3. **Endpoint IA** : URL de l'API IA (par défaut : Mistral AI)

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
