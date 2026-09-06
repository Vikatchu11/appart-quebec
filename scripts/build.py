#!/usr/bin/env python3
"""Construit le site, dans l'une ou l'autre de ses deux formes.

    python3 scripts/build.py            → site.html, un seul fichier avec les
                                          photos en base64 (pour l'Artifact,
                                          plafonné à 16 Mo)
    python3 scripts/build.py --web      → docs/, le site pour GitHub Pages :
                                          les photos restent des fichiers,
                                          en pleine qualité et sans limite

Lit data/quartiers.json, data/appartements.json et le dossier photos/.
"""
import base64, json, os, re, shutil, subprocess, sys, tempfile

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTOS = os.path.join(RACINE, "photos")
SORTIE = os.path.join(RACINE, "site.html")
CIBLE_MO = 13.5  # confort de chargement ; la limite dure des Artifacts est 16 Mo

# version web : plus de contrainte de poids, on vise la qualité
WEB = ((760, 72), (1800, 78))

# (largeur max, qualité) pour la vignette et pour la photo pleine taille
PALIERS = [((500, 52), (1150, 54)), ((470, 46), (1020, 46)), ((430, 40), (900, 38)),
           ((400, 34), (780, 32)), ((360, 30), (680, 28))]


def taille(chemin, _cache={}):
    """Plus grande dimension de l'image, pour ne jamais l'agrandir."""
    if chemin not in _cache:
        out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", chemin],
                             capture_output=True, text=True).stdout
        n = [int(m) for m in re.findall(r":\s*(\d+)", out)]
        _cache[chemin] = max(n) if n else 10000
    return _cache[chemin]


def encoder(chemin, largeur, qualite, cache):
    largeur = min(largeur, taille(chemin))
    cle = (chemin, largeur, qualite)
    if cle in cache:
        return cache[cle]
    tmp = os.path.join(tempfile.gettempdir(), "appart-build.jpg")
    subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(qualite),
         "-Z", str(largeur), chemin, "--out", tmp],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(tmp, "rb") as f:
        uri = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
    cache[cle] = uri
    return uri


def fichier_web(chemin, largeur, qualite, dossier, nom, _faits=set()):
    """Écrit une version redimensionnée dans docs/ et renvoie son chemin relatif."""
    largeur = min(largeur, taille(chemin))
    if (dossier, nom) in _faits:
        return dossier + "/" + nom
    _faits.add((dossier, nom))
    sortie = os.path.join(RACINE, "docs", dossier)
    os.makedirs(sortie, exist_ok=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(qualite),
                    "-Z", str(largeur), chemin, "--out", os.path.join(sortie, nom)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return dossier + "/" + nom


def construire(palier, web=False):
    (lv, qv), (lp, qp) = palier
    cache = {}
    manquantes = []

    quartiers = json.load(open(os.path.join(RACINE, "data/quartiers.json"), encoding="utf-8"))
    for qid, q in quartiers.items():
        # « _noel/photo.jpg » désigne le dossier commun photos/quartiers/_noel/
        for p in q.get("photos", []) + q.get("noel", []):
            partage = p["f"].startswith("_")
            chemin = os.path.join(PHOTOS, "quartiers", p["f"] if partage else os.path.join(qid, p["f"]))
            if not os.path.exists(chemin):
                manquantes.append(chemin); continue
            if web:
                dossier = "img/quartiers/" + (os.path.dirname(p["f"]) if partage else qid)
                base = os.path.splitext(os.path.basename(p["f"]))[0]
                p["vignette"] = fichier_web(chemin, lv, qv, dossier, base + "-v.jpg")
                p["image"] = fichier_web(chemin, lp, qp, dossier, base + "-p.jpg")
            else:
                p["vignette"] = encoder(chemin, lv, qv, cache)
                p["image"] = encoder(chemin, lp, qp, cache)

    doc = json.load(open(os.path.join(RACINE, "data/appartements.json"), encoding="utf-8"))
    for a in doc["appartements"]:
        images = []
        for photo in a.get("photos", []):
            if isinstance(photo, str):
                photo = {"f": photo}
            chemin = os.path.join(PHOTOS, "apparts", a["id"], photo["f"])
            if not os.path.exists(chemin):
                manquantes.append(chemin); continue
            if web:
                base = os.path.splitext(photo["f"])[0]
                dossier = "img/apparts/" + a["id"]
                images.append({"vignette": fichier_web(chemin, lv, qv, dossier, base + "-v.jpg"),
                               "image": fichier_web(chemin, lp, qp, dossier, base + "-p.jpg"),
                               "legende": photo.get("legende", "")})
            else:
                images.append({"vignette": encoder(chemin, lv, qv, cache),
                               "image": encoder(chemin, lp, qp, cache),
                               "legende": photo.get("legende", "")})
        a["images"] = images

    donnees = {"quartiers": quartiers, "appartements": doc["appartements"], "maj": doc.get("maj", "")}
    return donnees, manquantes


def page_web(gabarit, json_str, base_url=""):
    """Enveloppe le gabarit dans un vrai document HTML, avec l'aperçu de partage."""
    corps = gabarit.replace("/*__DONNEES__*/null", json_str)
    coupe = corps.index('<header class="barre">')
    tete, reste = corps[:coupe], corps[coupe:]
    partage = ""
    if base_url:
        partage = f"""<meta property="og:type" content="website">
<meta property="og:title" content="Notre appart à Québec">
<meta property="og:description" content="Les appartements repérés à Québec : photos, détails et l'ambiance des quartiers.">
<meta property="og:image" content="{base_url}/img/quartiers/montcalm/01-cartier-soir-p.jpg">
<meta property="og:url" content="{base_url}/">
<meta name="twitter:card" content="summary_large_image">
"""
    return ('<!doctype html>\n<html lang="fr">\n<head>\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="description" content="Les appartements repérés à Québec : photos, détails et l\'ambiance des quartiers.">\n'
            + partage + tete +
            '</head>\n<body>\n' + reste + '\n</body>\n</html>\n')


def main():
    gabarit = open(os.path.join(RACINE, "scripts/template.html"), encoding="utf-8").read()

    if "--web" in sys.argv:
        base_url = ""
        for i, a in enumerate(sys.argv):
            if a == "--base" and i + 1 < len(sys.argv):
                base_url = sys.argv[i + 1].rstrip("/")
        shutil.rmtree(os.path.join(RACINE, "docs/img"), ignore_errors=True)
        donnees, manquantes = construire(WEB, web=True)
        json_str = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
        os.makedirs(os.path.join(RACINE, "docs"), exist_ok=True)
        open(os.path.join(RACINE, "docs/index.html"), "w", encoding="utf-8").write(
            page_web(gabarit, json_str, base_url))
        open(os.path.join(RACINE, "docs/.nojekyll"), "w").close()
        total = sum(os.path.getsize(os.path.join(r, f))
                    for r, _, fs in os.walk(os.path.join(RACINE, "docs")) for f in fs)
        n_ph = sum(len(a["images"]) for a in donnees["appartements"]) + \
               sum(len(q["photos"]) + len(q.get("noel", [])) for q in donnees["quartiers"].values())
        print("docs/ — %.1f Mo · %d appartement(s) · %d photos"
              % (total / 1_048_576, len(donnees["appartements"]), n_ph))
        for m in manquantes:
            print("  photo introuvable :", m)
        return

    for i, palier in enumerate(PALIERS):
        donnees, manquantes = construire(palier)
        json_str = json.dumps(donnees, ensure_ascii=False).replace("</", "<\\/")
        page = gabarit.replace("/*__DONNEES__*/null", json_str)
        mo = len(page.encode()) / 1_048_576
        if mo <= CIBLE_MO or i == len(PALIERS) - 1:
            break
        print(f"  {mo:.1f} Mo — trop lourd, on recompresse…")
    open(SORTIE, "w", encoding="utf-8").write(page)
    n_app = len(donnees["appartements"])
    n_ph = sum(len(a["images"]) for a in donnees["appartements"]) + \
           sum(len(q["photos"]) for q in donnees["quartiers"].values())
    print(f"site.html — {mo:.1f} Mo · {n_app} appartement(s) · {n_ph} photos")
    for m in manquantes:
        print("  photo introuvable :", m)
    if mo > 16:
        print("  ATTENTION : au-dessus de la limite de 16 Mo des Artifacts.")


if __name__ == "__main__":
    main()
