# Backends IA

Deux backends interchangeables, sélectionnés dans **Fichier > Configuration > Mode IA**. L'étiquette en haut de la fenêtre affiche le mode actif en permanence.

## Modèle local (défaut)

Exécution **hors ligne** d'un modèle GGUF via `llama-cpp-python` — aucune clé API, aucun envoi de données.

| Taille | Modèle | Poids | RAM conseillée |
|---|---|---|---|
| `2gb` | Qwen2.5-3B-Instruct Q4_K_M | ~2 Go | 8 Go |
| `4gb` | Mistral-7B-Instruct-v0.3 Q4_K_M | ~4,4 Go | 8-12 Go |

- **Téléchargement** : `python download_model.py` (ou `python download_model.py 4gb`), une seule fois, dans `models/`
- **Chargement paresseux** : le modèle n'est chargé en mémoire qu'au premier clic de génération — l'UI démarre instantanément
- **Réglages** : taille du contexte (4096 par défaut) et threads CPU dans la configuration

Le Mistral-7B produit de meilleurs textes en français ; le Qwen 2 Go est plus rapide sur machine modeste.

## API distante

Endpoint de chat completions compatible **OpenAI/Mistral** (`src/ai/api_client.py`) :

- **Clé API** : ex. gratuite sur console.mistral.ai
- **Modèle** : `mistral-small-latest`, `gpt-4o-mini`…
- **Endpoint** : `https://api.mistral.ai/v1/chat/completions` par défaut

Idéal si ta machine est peu puissante ou si `llama-cpp-python` refuse de s'installer : ce mode ne requiert **ni modèle ni llama-cpp**.

## Bascule automatique

Au démarrage, si le mode est `local` mais que `llama-cpp-python` n'a pas pu s'installer, l'application : affiche un popup explicatif, bascule la config en mode API. Depuis un bouton de génération en mode local cassé, un dialogue propose aussi la bascule en un clic.

## Ce que l'IA génère

- **Noms / races / descriptions** (options à choisir)
- **Actions de combat** (noms + descriptions chiffrées, JSON contrôlé avec fallback DMG)
- **Scénario de rencontre** (contexte, tactique du monstre, ciblage, repli)
- **Correction orthographique** de tous les champs remplis

Les **statistiques chiffrées** (CA, PV, caractéristiques…) ne passent jamais par l'IA — voir [Génération des stats](Generation-stats.md).
