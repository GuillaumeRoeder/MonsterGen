# Rencontres

Le mode **Rencontre** (sélecteur « Mode : Fiche / Rencontre » en haut
de la fenêtre) permet de construire des
combats multi-monstres pour un groupe de joueurs, avec équilibrage
automatique selon les règles du Guide du Maître (ch. 9).

## Concepts : budget de PX et multiplicateurs

- **Budget de PX** : pour un groupe (joueurs, niveau moyen) et une
  difficulté (Facile / Moyen / Difficile / Mortel), le DMG donne un
  seuil de PX par personnage. Le budget de la rencontre est ce seuil
  multiplié par le nombre de joueurs.
- **PX ajustés** : les PX bruts d'une rencontre (somme des PX de tous
  les exemplaires) sont multipliés par un coefficient selon le nombre
  total de monstres : ×1 (1), ×1,5 (2), ×2 (3-5), ×2,5 (6-9), ×3
  (10-13), ×4 (14+). Six kobolds sont bien plus dangereux que six
  fois un kobold.
- **Difficulté réelle** : la difficulté la plus élevée dont le seuil
  est atteint par les PX ajustés — affichée en temps réel, en couleur,
  à côté du budget visé.

## Deux façons de construire une rencontre

### Description de la rencontre (contexte)

Le champ **« Description de la rencontre »** laisse le MJ décrire librement
le contexte : lieu, circonstances, composition des forces, armes des
monstres, éléments de décor... Cette description :

- est **intégrée telle quelle dans le prompt du scénario** : l'IA doit
  rendre le scénario cohérent avec ce contexte (armes mentionnées,
  disposition décrite, ambiance...) ;
- est **sauvegardée avec la rencontre** et restaurée au chargement ;
- est **optionnelle** : sans description, le scénario s'appuie uniquement
  sur les monstres, le groupe et la difficulté ;
- est **générable si vide** : le bouton « ✨ Générer » propose 3
  descriptions IA cohérentes avec la composition (monstres, quantités,
  difficulté) — le MJ en choisit une. « 🎲 Génération complète » remplit
  automatiquement une description vide avant de produire le scénario.

Exemple : « Embuscade de gobelins à l'arc dans un col montagneux au
 crépuscule ; leur chef brandit un totem tribal et crie des ordres en
 gobelin » → le scénario reprendra le col, les arcs, le crépuscule et
 le chef au totem.

### 1. Depuis la bibliothèque

1. Réglez le groupe (joueurs, niveau moyen, difficulté).
2. **＋ Ajouter depuis la bibliothèque** : sélection d'un ou plusieurs
   monstres sauvegardés (Ctrl+clic).
3. Les **quantités sont calculées automatiquement** pour converger
   vers le budget : un monstre fort sera seul, un monstre faible sera
   nombreux.
4. Les quantités restent **éditables à la main** dans le tableau ; le
   label de difficulté réelle se met à jour en temps réel.
5. **⚖ Ajuster les quantités** recalcule tout après un changement de
   groupe ou de difficulté.

### 2. Génération directe

- **✨ Générer un monstre** crée directement une nouvelle fiche
  équilibrée pour le CR correspondant à la difficulté visée (tables
  DMG pour les stats, IA pour le nom, la description et les actions),
  la sauvegarde dans la bibliothèque et l'ajoute à la rencontre.
- **🎲 Génération complète** prend la sélection courante, génère les
  fiches manquantes (monstres sans fiche dans la bibliothèque),
  ajuste les quantités et produit le scénario de rencontre.

## CR inadaptés à la difficulté : comment c'est géré

La sélection d'un monstre trop fort (ou trop faible) pour le budget
ne bloque jamais : le système **diagnostique** et **suggère**, le MJ
décide. Trois cas sont détectés par `check_selection` :

| Cas | Détection | Traitement |
|---|---|---|
| **Monstre trop fort** | Ses PX à lui seul dépassent le budget | Quantité figée à 1, message proposant : difficulté supérieure, monstre plus faible, ou rencontre mortelle délibérée |
| **Sélection trop lourde** | Total à 1 exemplaire chacun > 150 % du budget | Aucune multiplication ; suggestion de retirer des monstres ou de monter la difficulté |
| **Monstre trop faible** | Même 30 exemplaires n'atteignent pas la moitié du budget | Suggestion de difficulté inférieure ou de monstre plus fort |

Après ajustement des quantités, si les PX ajustés dépassent le budget
de plus de 10 %, le système **réduit d'abord les plus grands
groupes** (retirer un gobelin sur huit change moins l'ambiance que
retirer l'ogre).

Le tableau croisé complet :

- Chaque monstre rentre seul dans le budget → quantités ajustées,
  reliquat réparti.
- Un monstre dépasse le budget → quantité 1, diagnostic affiché.
- Tous les monstres sont trop faibles → diagnostic, mais la rencontre
  reste constructible (rencontre anecdotique assumée).
- Mélange fort/faible → le monstre fort reste seul, les faibles
  forment la masse : c'est le schéma « chef + sbires » classique.

## Scénario de rencontre

**📝 Générer le scénario** produit (via IA, locale ou API) un texte
pour le MJ avec les sections **Contexte**, **Disposition**,
**Tactique** (coordination entre monstres, ciblage, repli) et
**Récompense** — appuyé uniquement sur les monstres de la rencontre,
sans inventer de stats.

## Persistance et export

- **💾 Sauvegarder la rencontre** : JSON dans le dossier
  `rencontres/` du chemin de sauvegarde (monstres, quantités, groupe,
  difficulté, scénario).
- **📂 Charger une rencontre** : recharge la composition complète et
  rattache les fiches de la bibliothèque.
- **📄 Exporter les fiches (PDF)** : exporte en une fois un PDF par
  monstre de la rencontre (fiche de la bibliothèque si elle existe,
  sinon fiche générée à la volée pour le CR).

## Où est le code

- `src/rules/encounter_builder.py` — budgets, multiplicateurs,
  difficulté réelle, quantités suggérées, diagnostics de sélection,
  `build_auto_encounter`.
- `src/library/encounter_manager.py` — persistance des rencontres.
- `src/ui/encounter_tab.py` — le panneau UI du mode Rencontre (tableau, labels temps
  réel, dialogues de sélection).
- `src/ai/ai_generator.py::generate_encounter_scenario` — prompt du
  scénario multi-monstres.
