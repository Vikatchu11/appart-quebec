// Stockage partagé des notes (Netlify Blobs). GET renvoie les notes, PUT les remplace.
import { getStore } from "@netlify/blobs";

const VIDE = { victorien: {}, lou: {} };

export default async (req) => {
  const store = getStore("notes-appart");
  const entetes = { "cache-control": "no-store" };

  if (req.method === "GET") {
    const notes = (await store.get("partagees", { type: "json" })) || VIDE;
    return Response.json(notes, { headers: entetes });
  }

  if (req.method === "PUT") {
    let recu;
    try { recu = await req.json(); }
    catch { return Response.json({ erreur: "corps illisible" }, { status: 400, headers: entetes }); }

    const propre = { victorien: {}, lou: {} };
    for (const qui of ["victorien", "lou"]) {
      for (const [id, note] of Object.entries(recu?.[qui] || {})) {
        if (typeof note === "number" && note > 0 && note <= 5 && String(id).length < 80) {
          propre[qui][id] = note;
        }
      }
    }
    await store.setJSON("partagees", propre);
    return Response.json(propre, { headers: entetes });
  }

  return new Response("Méthode non gérée", { status: 405, headers: entetes });
};

export const config = { path: "/api/notes" };
