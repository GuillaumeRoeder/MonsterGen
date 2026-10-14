# Bibliothèque

Menu **Bibliothèque > Gérer les monstres sauvegardés** : mini gestionnaire des fiches enregistrées, sous forme de popup.

## Interface

- **Liste** : chaque sauvegarde affiche `Nom — CR x — date de modification` (fichiers illisibles signalés sans crash)
- **Dossier** affiché en haut de la popup (configurable dans la Configuration)

## Actions

| Bouton | Effet |
|---|---|
| 💾 **Sauvegarder le monstre actuel** | Nom de fichier pré-rempli avec le nom du monstre, **éditable** ; confirmation avant écrasement |
| 📂 **Charger** (ou double-clic) | Remplit l'éditeur ; confirmation si le monstre courant n'est pas sauvegardé |
| 🗑 **Supprimer** | Confirmation avant suppression définitive du fichier |

## Format des fichiers

Chaque monstre est un JSON autonome (`Monster.to_dict()`) : nom, stats, actions avec descriptions complètes, compétences, résistances, immunités, langues, scénario. Chargé tel quel via `Monster.from_dict()` — compatible entre versions tant que le schéma est respecté.
