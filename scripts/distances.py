#!/usr/bin/env python3
"""Calcule les trajets vers les points de repère et les écrit dans data/appartements.json.

    python3 scripts/distances.py

Utilise OSRM (données OpenStreetMap). À relancer après avoir ajouté un
appartement muni de son champ "coord" : [longitude, latitude].
"""
import json, os, subprocess, sys, time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FICHIER = os.path.join(RACINE, "data/appartements.json")

REPERES = {
    "vieux-quebec": {"nom": "Vieux-Québec", "coord": [-71.2050539, 46.8113081],
                     "lieu": "Château Frontenac"},
    "cegep-sainte-foy": {"nom": "Cégep de Sainte-Foy", "coord": [-71.2868410, 46.7866582],
                         "lieu": "2410, chemin Sainte-Foy"},
}
SERVEURS = {
    "voiture": "https://router.project-osrm.org/route/v1/driving/",
    "pied": "https://routing.openstreetmap.de/routed-foot/route/v1/foot/",
}


def trajet(base, depart, arrivee):
    url = "%s%s,%s;%s,%s?overview=false" % (base, depart[0], depart[1], arrivee[0], arrivee[1])
    out = subprocess.run(["curl", "-s", "--max-time", "40", "-A", "AppartQuebec/1.0", url],
                         capture_output=True, text=True).stdout
    d = json.loads(out)
    if d.get("code") != "Ok":
        raise RuntimeError(d.get("code", "réponse illisible"))
    r = d["routes"][0]
    return {"km": round(r["distance"] / 1000, 1), "min": round(r["duration"] / 60)}


def main():
    doc = json.load(open(FICHIER, encoding="utf-8"))
    for a in doc["appartements"]:
        if not a.get("coord"):
            print("  pas de coordonnées :", a["id"]); continue
        a["trajets"] = {}
        for cle, rep in REPERES.items():
            a["trajets"][cle] = {}
            for mode, base in SERVEURS.items():
                a["trajets"][cle][mode] = trajet(base, a["coord"], rep["coord"])
                time.sleep(0.6)
        r = a["trajets"]
        print("%-26s Vieux-Québec %4.1f km / %2d min auto, %3d min à pied  ·  Cégep %4.1f km / %2d min auto"
              % (a["id"], r["vieux-quebec"]["voiture"]["km"], r["vieux-quebec"]["voiture"]["min"],
                 r["vieux-quebec"]["pied"]["min"], r["cegep-sainte-foy"]["voiture"]["km"],
                 r["cegep-sainte-foy"]["voiture"]["min"]))
    json.dump(doc, open(FICHIER, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
