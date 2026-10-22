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
| 📥 **Importer** | Importe des monstres depuis un fichier (export groupé `{"monsters": [...]}`, liste JSON, ou fichier monstre individuel) |
| 🗑 **Supprimer** | Confirmation avant suppression définitive du fichier |

## Export / import de bibliothèque

- Menu **Export > Exporter la bibliothèque...** : cochage des monstres à exporter (tous décochés par défaut) puis écriture dans un **fichier unique** au format `{"monsters": [...]}`.
- Menu **Bibliothèque > Importer une bibliothèque...** (ou bouton 📥 de la popup) : copie les monstres du fichier dans le dossier de sauvegarde, un JSON par monstre (nom du monstre comme nom de fichier), avec avertissement en cas d'écrasement.

## Format des fichiers

Chaque monstre est un JSON autonome (`Monster.to_dict()`) : nom, stats, actions avec descriptions complètes, compétences, résistances, immunités, langues, scénario. Chargé tel quel via `Monster.from_dict()` — compatible entre versions tant que le schéma est respecté.
