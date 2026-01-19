import pandas as pd
import json
import os

def export_to_js():
    print("🔄 Lecture de TOUT l'historique CSV (28/12 -> Aujourd'hui)...")
    
    # 1. Vérification du fichier
    if not os.path.exists("historique_parkings.csv"):
        print("❌ ERREUR : Fichier 'historique_parkings.csv' introuvable.")
        return

    # 2. Lecture du CSV (tente différents encodages pour éviter les erreurs)
    try:
        df = pd.read_csv("historique_parkings.csv", sep=";", encoding='utf-8')
    except:
        try:
            df = pd.read_csv("historique_parkings.csv", sep=";", encoding='latin-1')
        except Exception as e:
            print(f"❌ Impossible de lire le fichier : {e}")
            return

    # 3. Nettoyage et Tri Chronologique
    # On reconstruit la date complète
    df['Datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Heure'], format='%Y-%m-%d %H:%M', errors='coerce')
    # On supprime les erreurs et on trie du plus vieux au plus récent
    df = df.dropna(subset=['Datetime']).sort_values('Datetime')

    print(f"   -> {len(df)} lignes trouvées dans le fichier.")
    if not df.empty:
        print(f"   -> Du {df['Datetime'].iloc[0]} au {df['Datetime'].iloc[-1]}")

    # 4. Dictionnaire GPS Complet (Tous les parkings identifiés)
    COORDS = {
        # PARKINGS VOITURE
        "antigone": [43.6087, 3.8888], "comedie": [43.6085, 3.8797], "corum": [43.6138, 3.8822],
        "europa": [43.6078, 3.8925], "foch": [43.6107, 3.8765], "gambetta": [43.6069, 3.8713],
        "gare": [43.6032, 3.8785], "triangle": [43.6092, 3.8818], "pitot": [43.6125, 3.8698],
        "circe": [43.6049, 3.9178], "garcia lorca": [43.5909, 3.8907], "mosson": [43.6162, 3.8196],
        "sabines": [43.5838, 3.8602], "sablassou": [43.6341, 3.9223], "saint jean le sec": [43.5708, 3.8379],
        "euromedecine": [43.6389, 3.8277], "occitanie": [43.6345, 3.8485], "vicarello": [43.6325, 3.8989],
        "gaumont": [43.6060, 3.9200], "charles de gaulle": [43.6285, 3.8977], "polygone": [43.6083, 3.8847],
        "arc de triomphe": [43.6112, 3.8724], 

        # STATIONS VÉLO
        "parvis jules ferry": [43.6035, 3.8788], "rue jules ferry": [43.6035, 3.8788],
        "pont de lattes": [43.5990, 3.8840], "deux ponts": [43.5980, 3.8850], "nouveau saint-roch": [43.5950, 3.8780],
        "albert 1er": [43.6145, 3.8730], "halles castellane": [43.6095, 3.8765], "observatoire": [43.6060, 3.8760],
        "rondelet": [43.6040, 3.8740], "plan cabanes": [43.6080, 3.8680], "boutonnet": [43.6230, 3.8670],
        "emile combes": [43.6180, 3.8850], "beaux-arts": [43.6160, 3.8830], "les aubes": [43.6150, 3.8950],
        "antigone centre": [43.6087, 3.8888], "médiathèque emile zola": [43.6080, 3.8930], "nombre d or": [43.6085, 3.8870],
        "louis blanc": [43.6150, 3.8750], "port marianne": [43.6000, 3.8990], "les arceaux": [43.6115, 3.8680],
        "cité mion": [43.6020, 3.8830], "renouvier": [43.6050, 3.8600], "odysseum": [43.6049, 3.9178],
        "saint-denis": [43.6050, 3.8710], "richter": [43.6030, 3.8950], "charles flahault": [43.6200, 3.8600],
        "voltaire": [43.6030, 3.8800], "prés d arènes": [43.5900, 3.8850], "vert bois": [43.6400, 3.8500],
        "malbosc": [43.6350, 3.8300], "facdessciences": [43.6310, 3.8610], "fac de lettres": [43.6315, 3.8700],
        "aiguelongue": [43.6250, 3.8800], "jeu de mail des abbés": [43.6200, 3.8850], "marie caizergues": [43.6200, 3.8750],
        "celleneuve": [43.6130, 3.8400], "jardin de la lironde": [43.6050, 3.9050], "père soulas": [43.6250, 3.8500],
        "place viala": [43.6180, 3.8550], "hôtel du département": [43.6220, 3.8500], "tonnelles": [43.6150, 3.8450],
        "providence": [43.5950, 3.8550], "pérols": [43.5650, 3.9600], "saint-guilhem": [43.6090, 3.8740],
        "sud de france": [43.5968, 3.9234], "comedie baudin": [43.6085, 3.8797], "jean de beins": [43.6070, 3.8850],
        "hôtel de ville": [43.5992, 3.8958]
    }

    output_data = []

    # 5. Traitement des données
    for (nom, type_p), group in df.groupby(['Nom', 'Type']):
        
        # Identification GPS
        lat, lon = None, None
        nom_clean = str(nom).lower()
        for key, val in COORDS.items():
            if key in nom_clean:
                lat, lon = val
                break
        
        if lat and lon:
            # Calcul du Statut (HS si écart-type nul)
            status = "HS" if group['Places_Libres'].std() == 0 else "OK"
            
            # --- MODIFICATION ICI : On prend TOUT, pas de limite .tail() ---
            # group = group  <-- On ne coupe rien.
            
            # Préparation des axes du graphique
            labels = group['Datetime'].dt.strftime('%d/%m %H:%M').tolist()
            
            occup = []
            for _, row in group.iterrows():
                try:
                    t = float(row['Places_Totales'])
                    l = float(row['Places_Libres'])
                    if t > 0:
                        occup.append(round((t - l) / t * 100))
                    else:
                        occup.append(0)
                except:
                    occup.append(0)

            # Dernière valeur pour l'affichage courant
            last = group.iloc[-1]

            output_data.append({
                "Nom": str(nom),
                "Type": str(type_p),
                "Lat": lat, "Lon": lon,
                "Status": status,
                "Libres": int(last['Places_Libres']),
                "Total": int(last['Places_Totales']),
                "History": {"Labels": labels, "Data": occup}
            })

    # 6. Écriture du fichier JS
    try:
        json_str = json.dumps(output_data, ensure_ascii=False)
        with open("data.js", "w", encoding="utf-8") as f:
            f.write(f"const realData = {json_str};")
        
        print(f"✅ Fichier 'data.js' généré avec SUCCÈS ({len(output_data)} parkings).")
        print("   -> Toutes les données du CSV ont été incluses.")

    except Exception as e:
        print(f"❌ Erreur écriture JS : {e}")

if __name__ == "__main__":
    export_to_js()
