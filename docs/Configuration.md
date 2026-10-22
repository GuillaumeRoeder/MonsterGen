# Configuration

Accessible via **Configuration**. Persistée dans `config/config.json` (chemin absolu, indépendant du répertoire de lancement).

## Mode IA

| Réglage | Description |
|---|---|
| Mode | Modèle local (hors ligne) ou API distante |
| Modèle local | Qwen 2 Go ou Mistral 4,4 Go |
| Chemin du modèle | Laisser vide pour `models/` automatique, ou pointer un `.gguf` tiers |
| Contexte | Taille du contexte du modèle (1024-32768, défaut 4096) |
| Threads CPU | 1-64 (défaut 4) |

## API distante

| Réglage | Description |
|---|---|
| Clé API | Requise pour le mode API |
| Modèle API | `mistral-small-latest` par défaut |
| Endpoint | Compatible OpenAI/Mistral |

## Divers

| Réglage | Description |
|---|---|
| Chemin de sauvegarde | Dossier de la [Bibliothèque](Bibliothèque.md) (`./fiches` par défaut) |

L'étiquette en haut de l'UI reflète immédiatement le mode après Sauvegarder.
