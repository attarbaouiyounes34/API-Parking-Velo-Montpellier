import pandas as pd
import folium
import plotly.graph_objects as go
import os
import unicodedata
import re
import json

# =========================
# SLUGIFY
# =========================
def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

# =========================
# DOSSIERS
# =========================
os.makedirs("pages", exist_ok=True)

# =========================
# LECTURE DES DONNÉES
# =========================
voitures_df = pd.read_csv("voitures.csv")
historique_df = pd.read_csv("historique_parkings.csv", sep=";")

with open("velos.csv", encoding="utf-8") as f:
    velos_geojson = json.load(f)

# =========================
# CAPACITÉS DE BASE
# =========================

# 🚗 Voitures (depuis voitures.csv)
capacite_voiture_base = (
    voitures_df
    .set_index("nom")["nb_places"]
    .to_dict()
)

# 🚲 Vélos (depuis le GeoJSON)
capacite_velo_base = {}
for feature in velos_geojson["features"]:
    props = feature["properties"]
    nom = props["name"]
    capacite = props.get("capacity") or props.get("nb_places")
    if capacite:
        capacite_velo_base[nom] = int(capacite)

# =========================
# DATETIME
# =========================
historique_df["datetime"] = pd.to_datetime(
    historique_df["Date"] + " " + historique_df["Heure"],
    errors="coerce"
)
historique_df = historique_df.dropna(subset=["datetime"])

# =========================
# SÉPARATION
# =========================
hist_voitures = historique_df[historique_df["Type"] == "Voiture"]
hist_velos = historique_df[historique_df["Type"] == "Velo"]

# =========================
# FONCTION PAGE HTML
# =========================
def create_page(nom, type_parking, fig_html=None, capacite=None):
    slug = slugify(nom)
    filename = f"pages/{slug}-{type_parking}.html"

    capacite_html = (
        f"<h3>Capacité : {capacite} places</h3>"
        if capacite is not None else ""
    )

    if fig_html:
        content = capacite_html + fig_html
    else:
        content = capacite_html + """
        <div style="padding:20px; background:#f8f8f8; border:1px solid #ccc;">
            <h3>⚠️ Aucune donnée disponible</h3>
            <p>Il n’existe pas encore d’historique pour ce parking.</p>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{nom} – {type_parking}</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 20px;
}}
.footer {{
    margin-top: 30px;
}}
button {{
    padding: 10px 15px;
    font-size: 16px;
    cursor: pointer;
}}
</style>
</head>
<body>

<h1>{"🚗" if type_parking=="voiture" else "🚲"} {nom}</h1>

{content}

<div class="footer">
    <a href="../carte_parkings.html">
        <button>⬅ Retour à la carte</button>
    </a>
</div>

</body>
</html>
"""

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

# =========================
# GRAPHIQUES + PAGES VOITURE
# =========================
print("🚗 Pages parkings voiture...")

for nom in voitures_df["nom"].unique():
    data = hist_voitures[hist_voitures["Nom"] == nom].copy()
    fig_html = None

    capacite = capacite_voiture_base.get(nom)

    if not data.empty:
        data = data.dropna(subset=["Places_Libres", "Places_Totales"])
        if not data.empty:
            if capacite is None:
                capacite = int(data["Places_Totales"].max())
            else:
                capacite = int(capacite)

            data["Places_Libres"] = data["Places_Libres"].clip(0, capacite)
            data["voitures"] = capacite - data["Places_Libres"]

            data = (
                data.set_index("datetime")[["voitures"]]
                .resample("5min")
                .mean()
                .dropna()
            )

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data["voitures"],
                fill="tozeroy",
                name="Voitures"
            ))

            fig.add_hline(
                y=capacite,
                line_dash="dash",
                line_color="orange",
                annotation_text=f"Capacité {capacite}",
                annotation_position="top left"
            )

            fig.update_layout(
                template="plotly_white",
                xaxis_title="Temps",
                yaxis_title="Nombre de voitures",
                hovermode="x unified"
            )

            fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

    create_page(nom, "voiture", fig_html, capacite)

# =========================
# GRAPHIQUES + PAGES VÉLO
# =========================
print("🚲 Pages parkings vélo...")

for feature in velos_geojson["features"]:
    nom = feature["properties"]["name"]
    data = hist_velos[hist_velos["Nom"] == nom].copy()
    fig_html = None

    capacite = capacite_velo_base.get(nom)

    if not data.empty:
        data = data.dropna(subset=["Places_Libres", "Places_Totales"])
        if not data.empty:
            if capacite is None:
                capacite = int(data["Places_Totales"].max())
            else:
                capacite = int(capacite)

            data["velos"] = capacite - data["Places_Libres"]

            data = (
                data.set_index("datetime")[["velos"]]
                .resample("5min")
                .mean()
                .dropna()
            )

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data.index,
                y=data["velos"],
                fill="tozeroy",
                line=dict(color="green"),
                name="Vélos"
            ))

            fig.add_hline(
                y=capacite,
                line_dash="dash",
                line_color="black",
                annotation_text=f"Capacité {capacite}"
            )

            fig.update_layout(
                template="plotly_white",
                xaxis_title="Temps",
                yaxis_title="Nombre de vélos"
            )

            fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)

    create_page(nom, "velo", fig_html, capacite)

# =========================
# CARTE FOLIUM
# =========================
print("🗺️ Carte interactive...")

m = folium.Map(location=[43.6108, 3.8767], zoom_start=13)

# 🚗 Voitures
for _, row in voitures_df.iterrows():
    if pd.isna(row["Ylat"]) or pd.isna(row["Xlong"]):
        continue

    nom = row["nom"]
    capacite = capacite_voiture_base.get(nom, "N/A")
    slug = slugify(nom)

    folium.Marker(
        [row["Ylat"], row["Xlong"]],
        tooltip=f"🚗 {nom}",
        popup=f"""
        <b>🚗 {nom}</b><br>
        Capacité : {capacite} places<br><br>
        <a href="pages/{slug}-voiture.html" target="_blank">
            Voir l'occupation
        </a>
        """,
        icon=folium.Icon(icon="car", prefix="fa", color="blue")
    ).add_to(m)

# 🚲 Vélos
for feature in velos_geojson["features"]:
    nom = feature["properties"]["name"]
    lon, lat = feature["geometry"]["coordinates"]
    capacite = capacite_velo_base.get(nom, "N/A")
    slug = slugify(nom)

    folium.Marker(
        [lat, lon],
        tooltip=f"🚲 {nom}",
        popup=f"""
        <b>🚲 {nom}</b><br>
        Capacité : {capacite} places<br><br>
        <a href="pages/{slug}-velo.html" target="_blank">
            Voir l'occupation
        </a>
        """,
        icon=folium.Icon(icon="bicycle", prefix="fa", color="green")
    ).add_to(m)

m.save("carte_parkings.html")

print("🎉 TERMINÉ – capacités cohérentes, graphiques fiables, popups complets")
