# Inférence de traits

Le module `src/rules/trait_inference.py` analyse la **race et la description** du monstre (et le texte des actions existantes) pour rendre les stats générées crédibles par rapport au concept. Détection par mots-clés en français, insensible aux accents.

## Archétypes

La race pèse double par rapport à la description. Cinq archétypes déterminent l'ordre de priorité des caractéristiques :

| Archétype | Mots-clés (exemples) | Priorité stats |
|---|---|---|
| **brute** | ogre, massif, barbare, hache… | FOR > CON > CHA |
| **sneaky** | voleur, furtif, dague, poison… | DEX > CON > CHA |
| **caster** | mage, arcane, sorts… | INT > CON > SAG |
| **divin** | prêtre, temple, céleste… | SAG > CON > CHA |
| **charismatique** | barde, roi, diplomate… | CHA > CON > SAG |

## Ce qui est déduit

- **Armes** : « hache » → hache de bataille ; « griffes/mords » → attaques naturelles ; « lance des sorts » est correctement ignoré. Les armes détectées remplacent le tirage aléatoire
- **Action spéciale** : type de dégâts (feu, froid, foudre, poison…) et nom (Souffle, Hurlement…) selon les mots-clés
- **Vitesse** : vol (ailes), nage (aquatique), fouisse, grimpe ; « rapide » → 12 m, « massif/golem » → 6 m
- **Compétences maîtrisées** : base par archétype (brute → Athlétisme/Intimidation) + mots-clés (chasse → Survie, forêt → Nature…), max 4
- **Résistances/immunités** : double condition — un signal (« résiste », « peau dure » → résistance ; « immunisé », « carapace » → immunité) **et** un type de dégâts cité dans le texte. Rien n'est inventé sans les deux

## Exemples

```
infer_traits("Ogre", "créature massive à la peau dure qui résiste au feu")
→ archetype=brute, résistances=[feu], armes=[], compétences=[Athlétisme, Intimidation]

infer_traits("Dragon", "dragon rouge au souffle de feu, volant dans le ciel")
→ special_damage=feu, special_name=Souffle, speed=vol 9 m
```

Les valeurs déjà saisies par l'utilisateur ne sont **jamais écrasées** : l'inférence ne remplit que les champs vides.
