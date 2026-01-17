import pandas as pd
import folium
import plotly.graph_objects as go
import os
import unicodedata
import re
import xml.etree.ElementTree as ET

# ==========================================
# 1. UTILITAIRES & CONFIGURATION
# ==========================================
def slugify(text):
    if not isinstance(text, str): return "sans-nom"
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

os.makedirs("pages", exist_ok=True)

# ==========================================
# 2. LECTURE DU KML (PARKINGS)
# ==========================================
def parse_kml(kml_file):
    print(f"📖 Lecture de {kml_file}...")
    try:
        tree = ET.parse(kml_file)
        root = tree.getroot()
        # Le namespace est crucial pour le format KML
        namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        data_list = []
        for placemark in root.findall('.//kml:Placemark', namespace):
            parking_info = {}
            # Extraction des données descriptives
            for data in placemark.findall('.//kml:SimpleData', namespace):
                name = data.get('name')
                parking_info[name] = data.text
            
            # Extraction et correction des coordonnées (évite l'erreur d'unpacking)
            coords_text = placemark.find('.//kml:coordinates', namespace).text.strip()
            parts = coords_text.split(',')
            if len(parts) >= 2:
                parking_info['Xlong'] = float(parts[0])
                parking_info['Ylat'] = float(parts[1])
                data_list.append(parking_info)
        
        df = pd.DataFrame(data_list)
        # Nettoyage des types numériques
        numeric_cols = ["nb_places", "nb_pmr", "places_pub"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du KML : {e}")
        return pd.DataFrame()

# ==========================================
# 3. LECTURE DE L'HISTORIQUE (CSV)
# ==========================================
print("📖 Lecture de l'historique...")
historique_df = pd.read_csv("historique_parkings.csv", sep=";")
historique_df["datetime"] = pd.to_datetime(
    historique_df["Date"] + " " + historique_df["Heure"], 
    errors="coerce"
)
historique_df = historique_df.dropna(subset=["datetime"])

# Charger les infos depuis le KML
voitures_df = parse_kml("parkings.kml")

# ==========================================
# 4. GÉNÉRATION DES PAGES INDIVIDUELLES
# ==========================================
def create_parking_page(info_parking):
    nom = info_parking["nom"]
    slug = slugify(nom)
    filename = f"pages/{slug}-voiture.html"
    capacite = int(info_parking['nb_places'])
    
    # Filtrer l'historique pour ce parking
    data_hist = historique_df[(historique_df["Nom"] == nom) & (historique_df["Type"] == "Voiture")].copy()
    
    fig_html = ""
    if not data_hist.empty:
        # 1. Calcul de l'occupation
        data_hist["occupés"] = capacite - data_hist["Places_Libres"]
        
        # 2. ON NE GARDE QUE LES COLONNES NUMÉRIQUES AVANT LE RESAMPLE
        # C'est ici que l'erreur se corrige
        data_hist = data_hist.set_index("datetime")
        data_hist = data_hist[["occupés"]].resample("5min").mean().dropna()

        if not data_hist.empty:
            # ... la suite du code pour le graphique reste identique
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=data_hist.index, y=data_hist["occupés"],
                fill="tozeroy", name="Véhicules", line=dict(color="#3498db")
            ))
            fig.add_hline(y=capacite, line_dash="dash", line_color="red", 
                          annotation_text=f"Capacité max: {capacite}")
            
            fig.update_layout(
                title=f"Tendance d'occupation : {nom}",
                template="plotly_white",
                xaxis_title="Temps",
                yaxis_title="Places occupées",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
    
    if not fig_html:
        fig_html = """<div style="padding:20px; background:#fef3c7; border-radius:8px;">
                        <b>ℹ️ Note :</b> Aucune donnée historique trouvée pour ce parking.</div>"""

    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>{nom} - Détails</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; line-height: 1.6; color: #333; }}
            .card {{ border: 1px solid #ddd; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            button {{ background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }}
            button:hover {{ background: #2980b9; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>🚗 Parking {nom}</h1>
            <p>📍 <b>Adresse :</b> {info_parking.get('adresse', 'Non renseignée')}</p>
            <p>📊 <b>Capacité :</b> {capacite} places (dont {info_parking.get('nb_pmr', 0)} PMR)</p>
            <p>🏢 <b>Type :</b> {info_parking.get('type_ouvra', 'N/A')} - {info_parking.get('proprietai', '')}</p>
            <hr>
            {fig_html}
            <div style="margin-top: 30px;">
                <a href="../carte_parkings.html"><button>⬅ Retour à la carte</button></a>
            </div>
        </div>
    </body>
    </html>
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)

print("📊 Génération des pages HTML...")
for _, row in voitures_df.iterrows():
    create_parking_page(row)

# ==========================================
# 5. CARTE FOLIUM PRINCIPALE
# ==========================================
print("🗺️ Création de la carte interactive...")
# Centré sur Montpellier
m = folium.Map(
    location=[43.6108, 3.8767], 
    zoom_start=14, 
    tiles='OpenStreetMap'
)
for _, row in voitures_df.iterrows():
    slug = slugify(row["nom"])
    
    popup_content = f"""
    <div style="width:220px; font-family: sans-serif;">
        <h4 style="margin-bottom:5px;">🚗 {row['nom']}</h4>
        <p style="font-size:12px; color:#666;">{row['adresse']}</p>
        <hr>
        <b>Capacité :</b> {row['nb_places']} places<br>
        <b>PMR :</b> {row['nb_pmr']}<br><br>
        <a href="pages/{slug}-voiture.html" target="_blank" 
           style="display:inline-block; background:#3498db; color:white; padding:8px 12px; text-decoration:none; border-radius:4px; font-weight:bold; width:90%; text-align:center;">
           📈 Voir l'occupation
        </a>
    </div>
    """
    
    folium.Marker(
        location=[row["Ylat"], row["Xlong"]],
        popup=folium.Popup(popup_content, max_width=250),
        tooltip=row["nom"],
        icon=folium.Icon(color="blue", icon="car", prefix="fa")
    ).add_to(m)

m.save("carte_parkings.html")
print("🎉 TERMINÉ ! Ouvrez 'carte_parkings.html' pour voir le résultat.")