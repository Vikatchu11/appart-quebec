# Notre appart à Québec

Site d'une seule page qui liste les appartements repérés, avec toutes leurs photos,
leurs détails, et les photos des trois quartiers visés.

En ligne : https://claude.ai/code/artifact/f139503c-dc39-4e9b-aa44-8a790c021386
(privé par défaut — il faut le partager depuis le menu « Partager » de la page.)

## Le contenu

    data/appartements.json   la liste des appartements (c'est le fichier à remplir)
    data/quartiers.json      les 3 quartiers : textes, repères, photos, crédits
    photos/quartiers/…       photos des quartiers (17, sous licence libre)
    photos/apparts/<id>/…    photos d'un appartement, une dossier par annonce
    scripts/template.html    le gabarit du site (design + interactions)
    scripts/build.py         assemble tout dans site.html
    site.html                le fichier final, photos incluses — c'est lui qu'on publie

## Ajouter un appartement

1. Créer le dossier des photos : `photos/apparts/<id>/` (`01.jpg`, `02.jpg`, …).
2. Ajouter une entrée dans `data/appartements.json` :

```json
{
  "id": "fraser-1234",
  "titre": "4½ sur l'avenue Fraser",
  "adresse": "1234, avenue Fraser",
  "quartier": "montcalm",
  "loyer": 1650,
  "charges": "Chauffage et eau chaude inclus",
  "pieces": "4½",
  "chambres": 2,
  "superficie": 78,
  "etage": "2e",
  "meuble": false,
  "dispo": "2026-07-01",
  "bail": "12 mois",
  "atouts": ["Balcon plein sud", "Lave-vaisselle"],
  "bemols": ["Pas de stationnement"],
  "notes": "Visite possible en semaine après 17 h.",
  "lien": "https://…",
  "source": "Centris",
  "statut": "a_visiter",
  "photos": [
    {"f": "01.jpg", "legende": "Le salon"},
    {"f": "02.jpg", "legende": "La cuisine"}
  ]
}
```

Tout est facultatif sauf `id`, `titre`, `quartier` et `photos`.
`quartier` vaut `montcalm`, `sillery`, `saint-sacrement`, `saint-jean-baptiste`,
`maizerets` ou `loretteville`.
`statut` vaut `a_visiter`, `visite_prevue`, `visite` ou `ecarte`.

3. Ajouter `"coord": [longitude, latitude]` (relevé sur OpenStreetMap ou Google
   Maps), puis calculer les distances vers le Vieux-Québec et le Cégep de
   Sainte-Foy :

```
python3 scripts/distances.py
```

4. Reconstruire :

```
python3 scripts/build.py
```

5. Republier `site.html` (même adresse, Lou n'a pas besoin d'un nouveau lien).

## Les notes

Chaque appartement se note sur 5 : une ligne pour Victorien, une pour Lou, plus la
moyenne. Les deux lignes sont cliquables sur n'importe quel appareil — pas de
compte, pas d'étape préalable.

Les notes sont gardées dans le navigateur (`localStorage`) : une page publiée ne
peut pas les synchroniser toute seule sans restreindre le partage du lien. Pour
les mettre en commun : « Copier nos notes » donne un code d'une ligne
(`APPART1.…`) à envoyer, que l'autre colle dans « Coller les notes reçues ».

## Le poids des photos

Les photos sont encodées dans `site.html`, et un Artifact est limité à 16 Mo.
`build.py` recompresse automatiquement tout le monde d'un cran quand la page
dépasse 10,5 Mo, et l'affiche à la fin de son exécution. En pratique : environ 300 Ko par photo dans la page finale, donc viser 6 à 10
photos par appartement. À partir de 4 ou 5 annonces on approchera de la limite —
il faudra alors héberger le site ailleurs (GitHub Pages, Netlify), où les photos
restent des fichiers séparés et où il n'y a plus de plafond.
