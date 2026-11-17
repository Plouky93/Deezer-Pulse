import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sqlite3
import time
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Deezer Pulse • Studio", page_icon="✦", layout="wide")

# --- DIRECTION ARTISTIQUE : OLED & APPLE GLASSMORPHISM ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }

    .stApp {
        background-color: #000000;
        background-image: 
            radial-gradient(circle at 12% 10%, rgba(120, 40, 200, 0.24) 0%, transparent 38%),
            radial-gradient(circle at 88% 20%, rgba(235, 50, 120, 0.18) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(20, 110, 245, 0.18) 0%, transparent 48%);
        background-attachment: fixed;
        color: #F5F5F7;
    }

    header[data-testid="stHeader"] { background: transparent; }

    section[data-testid="stSidebar"] {
        background-color: rgba(10, 10, 13, 0.88);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Cartes KPI Glassmorphism */
    div[data-testid="stMetric"] {
        background: rgba(22, 22, 26, 0.55);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 18px 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.16);
        transition: transform 0.25s ease, border-color 0.25s ease;
    }

    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: rgba(255, 255, 255, 0.32);
    }

    div[data-testid="stMetricLabel"] {
        color: #98989D !important;
        font-size: 0.78rem !important;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 1.95rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    /* Cartes Podium & Recommandations */
    .glass-card {
        background: rgba(24, 24, 29, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
        transition: transform 0.25s ease;
        height: 100%;
    }
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 55, 95, 0.5);
    }
    .glass-card img {
        border-radius: 14px;
        width: 100%;
        box-shadow: 0 8px 20px rgba(0,0,0,0.5);
        margin-bottom: 12px;
    }
    .card-rank {
        font-size: 0.75rem;
        font-weight: 700;
        color: #FF375F;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 4px 0 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .card-sub {
        font-size: 0.85rem;
        color: #A1A1A6;
        margin-bottom: 6px;
    }

    /* Onglets stylisés */
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #A1A1A6 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
    }

    h1 {
        background: linear-gradient(135deg, #FFFFFF 0%, #9E9EA9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
    }

    div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {
        background: rgba(18, 18, 22, 0.5);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- BASE DE CACHE SQLITE ENRICHIE ---
def init_db():
    conn = sqlite3.connect("deezer_cache.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks_meta (
            artist TEXT, title TEXT, bpm REAL, release_date TEXT, 
            rank INTEGER, cover_url TEXT, artist_id INTEGER,
            PRIMARY KEY (artist, title)
        )
    """)
    conn.commit()
    return conn

def get_deezer_metadata(artist, title, album, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT bpm, release_date, rank, cover_url, artist_id FROM tracks_meta WHERE artist=? AND title=?", (artist, title))
    cached = cursor.fetchone()
    if cached:
        return {"bpm": cached[0], "release_date": cached[1], "rank": cached[2], "cover_url": cached[3], "artist_id": cached[4]}

    try:
        query = f"{artist} {title} {album}" if pd.notna(album) and str(album).strip() != "" else f"{artist} {title}"
        res = requests.get("https://api.deezer.com/search", params={"q": query, "limit": 1}, timeout=5).json()
        if res.get("data"):
            item = res["data"][0]
            track_id = item["id"]
            artist_id = item.get("artist", {}).get("id", 0)
            cover_url = item.get("album", {}).get("cover_xl") or item.get("album", {}).get("cover_big") or ""
            
            details = requests.get(f"https://api.deezer.com/track/{track_id}", timeout=5).json()
            bpm = details.get("bpm", 0)
            release_date = details.get("release_date", "Inconnue")
            rank = details.get("rank", 0)

            cursor.execute(
                "INSERT OR REPLACE INTO tracks_meta VALUES (?, ?, ?, ?, ?, ?, ?)",
                (artist, title, bpm, release_date, rank, cover_url, artist_id)
            )
            conn.commit()
            time.sleep(0.1)
            return {"bpm": bpm, "release_date": release_date, "rank": rank, "cover_url": cover_url, "artist_id": artist_id}
    except Exception:
        pass
    return {"bpm": 0, "release_date": "Inconnue", "rank": 0, "cover_url": "", "artist_id": 0}

@st.cache_data(ttl=3600, show_spinner=False)
def generate_smart_recommendations(top_artist_ids, known_artists_lower):
    """Moteur de découverte : explore les artistes similaires non encore écoutés."""
    recos = []
    seen_artists = set(known_artists_lower)

    for aid in top_artist_ids:
        if not aid or aid == 0:
            continue
        try:
            rel_res = requests.get(f"https://api.deezer.com/artist/{aid}/related", params={"limit": 6}, timeout=5).json()
            for rel_artist in rel_res.get("data", []):
                r_name = rel_artist.get("name", "")
                r_id = rel_artist.get("id")
                if r_name.lower() in seen_artists:
                    continue
                seen_artists.add(r_name.lower())

                # Récupérer le morceau phare et l'album associé
                top_tracks = requests.get(f"https://api.deezer.com/artist/{r_id}/top", params={"limit": 1}, timeout=5).json()
                if top_tracks.get("data"):
                    t = top_tracks["data"][0]
                    recos.append({
                        "artist": r_name,
                        "track": t.get("title"),
                        "album": t.get("album", {}).get("title"),
                        "cover": t.get("album", {}).get("cover_xl") or rel_artist.get("picture_xl"),
                        "preview": t.get("preview"),
                        "fans": rel_artist.get("nb_fan", 0)
                    })
                time.sleep(0.08)
        except Exception:
            continue
    return recos[:8]

# --- GESTION DE LA SAUVEGARDE LOCALE ---
SAVE_FILE = "saved_history.pkl"

with st.sidebar:
    st.markdown("### ⚙️ Source des données")
    uploaded_file = st.file_uploader("Importer / Mettre à jour (CSV ou XLSX)", type=["csv", "xlsx"])
    if os.path.exists(SAVE_FILE):
        st.success("Données en mémoire actives")
        if st.button("🗑️ Effacer la mémoire"):
            os.remove(SAVE_FILE)
            st.rerun()

df = None
if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        xl = pd.ExcelFile(uploaded_file)
        sheet = "10_listeningHistory" if "10_listeningHistory" in xl.sheet_names else xl.sheet_names[0]
        df = pd.read_excel(uploaded_file, sheet_name=sheet)
    df.to_pickle(SAVE_FILE)
elif os.path.exists(SAVE_FILE):
    df = pd.read_pickle(SAVE_FILE)

# --- EN-TÊTE ---
st.title("Deezer Pulse")
st.caption("STUDIO ANALYTIQUE & MOTEUR DE DÉCOUVERTE • ÉDITION OLED")

if df is not None:
    df["Date"] = pd.to_datetime(df["Date"])
    df["Heure"] = df["Date"].dt.hour
    df["Jour_Num"] = df["Date"].dt.dayofweek
    jours_fr = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
    df["Jour"] = df["Jour_Num"].map(jours_fr)

    ecoutes_valides = df[df["Listening Time"] >= 30].copy()
    zaps = df[df["Listening Time"] < 30].copy()

    conn = init_db()
    uniques = ecoutes_valides[["Artist", "Song Title", "Album"]].drop_duplicates(subset=["Artist", "Song Title"])
    
    progress_bar = st.progress(0, text="Synchronisation des pochettes & métadonnées...")
    meta_dict = {}
    for i, (_, row) in enumerate(uniques.iterrows()):
        key = (row["Artist"], row["Song Title"])
        meta_dict[key] = get_deezer_metadata(row["Artist"], row["Song Title"], row.get("Album", ""), conn)
        progress_bar.progress((i + 1) / len(uniques))
    progress_bar.empty()
    conn.close()

    ecoutes_valides["bpm"] = ecoutes_valides.apply(lambda r: meta_dict[(r["Artist"], r["Song Title"])]["bpm"], axis=1)
    ecoutes_valides["release_date"] = ecoutes_valides.apply(lambda r: meta_dict[(r["Artist"], r["Song Title"])]["release_date"], axis=1)
    ecoutes_valides["cover_url"] = ecoutes_valides.apply(lambda r: meta_dict[(r["Artist"], r["Song Title"])]["cover_url"], axis=1)
    ecoutes_valides["artist_id"] = ecoutes_valides.apply(lambda r: meta_dict[(r["Artist"], r["Song Title"])]["artist_id"], axis=1)
    ecoutes_valides["Annee"] = pd.to_datetime(ecoutes_valides["release_date"], errors="coerce").dt.year

    # --- NAVIGATION PAR ONGLETS ---
    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "🔬 Data Science & Comportement", "✨ Découvertes Sur-Mesure"])

    # ==========================================
    # ONGLET 1 : VUE D'ENSEMBLE & PODIUM HD
    # ==========================================
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        # KPIs
        col1, col2, col3, col4, col5 = st.columns(5)
        total_h = ecoutes_valides["Listening Time"].sum() / 3600
        ratio_fidelite = len(ecoutes_valides) / max(1, len(uniques))
        bpm_valides = ecoutes_valides[ecoutes_valides["bpm"] > 0]["bpm"]

        col1.metric("Temps d'écoute", f"{total_h:.1f} h")
        col2.metric("Titres validés", f"{len(ecoutes_valides)}", f"{len(zaps)} zappés", delta_color="off")
        col3.metric("Indice Fidélité", f"{ratio_fidelite:.1f}x", "écoutes / titre", delta_color="off")
        col4.metric("Tempo Moyen", f"{bpm_valides.mean():.0f} BPM" if not bpm_valides.empty else "—")
        col5.metric("Époque Moyenne", f"{ecoutes_valides['Annee'].mean():.0f}" if ecoutes_valides["Annee"].notna().any() else "—")

        # Podium Top 3 Albums avec Pochettes HD
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🏆 Podium des Albums")
        top_albums = (
            ecoutes_valides.groupby(["Album", "Artist", "cover_url"], as_index=False)["Listening Time"]
            .sum()
            .sort_values(by="Listening Time", ascending=False)
            .head(3)
        )
        p_cols = st.columns(3)
        medals = ["01 • EN BOUCLE", "02 • INCONTOURNABLE", "03 • RÉFÉRENCE"]
        for idx, (_, alb) in enumerate(top_albums.iterrows()):
            with p_cols[idx]:
                img_src = alb["cover_url"] if alb["cover_url"] else "https://e-cdns-images.dzcdn.net/images/cover/d41d8cd98f00b204e9800998ecf8427e/500x500-000000-80-0-0.jpg"
                mins = alb["Listening Time"] / 60
                st.markdown(f"""
                <div class="glass-card">
                    <div class="card-rank">{medals[idx]}</div>
                    <img src="{img_src}" alt="cover">
                    <div class="card-title">{alb['Album']}</div>
                    <div class="card-sub">{alb['Artist']} • {mins:.1f} min</div>
                </div>
                """, unsafe_allow_html=True)

        # Graphiques principaux
        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Top Artistes (Minutes)")
            top_art = (ecoutes_valides.groupby("Artist")["Listening Time"].sum().sort_values(ascending=True).tail(8) / 60).reset_index()
            fig_art = px.bar(top_art, x="Listening Time", y="Artist", orientation="h", color="Listening Time", color_continuous_scale=["#5E5CE6", "#BF5AF2", "#FF375F"])
            fig_art.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E5EA"), coloraxis_showscale=False, xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=""), yaxis=dict(showgrid=False, title=""), margin=dict(l=10, r=10, t=10, b=10), height=300)
            st.plotly_chart(fig_art, use_container_width=True)

        with g2:
            st.subheader("Rythme Circadien (Écoutes / Heure)")
            heures_completes = pd.DataFrame({"Heure": range(24)})
            par_heure = ecoutes_valides.groupby("Heure")["Listening Time"].count().reset_index()
            par_heure = heures_completes.merge(par_heure, on="Heure", how="left").fillna(0)
            fig_heure = go.Figure(go.Scatter(x=par_heure["Heure"], y=par_heure["Listening Time"], mode="lines+markers", line=dict(color="#30D158", width=3, shape="spline"), marker=dict(size=6, color="#FFFFFF", line=dict(width=2, color="#30D158")), fill="tozeroy", fillcolor="rgba(48, 209, 88, 0.15)"))
            fig_heure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E5EA"), xaxis=dict(showgrid=False, tickmode="linear", dtick=3, title="", ticksuffix="h"), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=""), margin=dict(l=10, r=10, t=10, b=10), height=300)
            st.plotly_chart(fig_heure, use_container_width=True)

        # Classement Titres
        st.subheader("Classement des Titres")
        top_titres = (
            ecoutes_valides.groupby(["Artist", "Song Title", "Album", "bpm", "release_date"], as_index=False)
            .agg(Écoutes=("Listening Time", "count"), Minutes=("Listening Time", lambda x: round(x.sum() / 60, 1)))
            .sort_values(by=["Minutes", "Écoutes"], ascending=False)
        )
        st.dataframe(top_titres, use_container_width=True, hide_index=True)

    # ==========================================
    # ONGLET 2 : DATA SCIENCE & COMPORTEMENT
    # ==========================================
    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        # Heatmap Jour x Heure
        st.subheader("🌡️ Empreinte Temporelle (Jour × Heure)")
        ordre_jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        pivot_heat = ecoutes_valides.pivot_table(index="Jour", columns="Heure", values="Listening Time", aggfunc="count", fill_value=0)
        pivot_heat = pivot_heat.reindex(index=ordre_jours, columns=range(24), fill_value=0)

        fig_heat = px.imshow(
            pivot_heat,
            labels=dict(x="Heure", y="Jour", color="Écoutes"),
            x=[f"{h}h" for h in range(24)],
            y=ordre_jours,
            color_continuous_scale=["#0A0A0C", "#3A1C71", "#D76D77", "#FFAF7B"],
            aspect="auto"
        )
        fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E5EA"), margin=dict(l=10, r=10, t=10, b=10), height=280)
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        ds1, ds2, ds3 = st.columns(3)

        # Répartition par Support (Donut Néon)
        with ds1:
            st.subheader("📱 Supports d'écoute")
            if "Platform" in ecoutes_valides.columns:
                plat_df = ecoutes_valides.groupby("Platform")["Listening Time"].sum().reset_index()
                fig_plat = px.pie(plat_df, values="Listening Time", names="Platform", hole=0.62, color_discrete_sequence=["#0A84FF", "#BF5AF2", "#30D158", "#FF9F0A"])
                fig_plat.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E5EA"), margin=dict(l=10, r=10, t=10, b=10), height=280, showlegend=True)
                st.plotly_chart(fig_plat, use_container_width=True)

        # Répartition par Décennie
        with ds2:
            st.subheader("⏳ Décennies Musicales")
            ecoutes_valides["Decennie"] = (ecoutes_valides["Annee"] // 10 * 10).dropna().astype(int).astype(str) + "s"
            dec_df = ecoutes_valides[ecoutes_valides["Decennie"] != "nans"].groupby("Decennie")["Listening Time"].count().reset_index()
            fig_dec = px.bar(dec_df, x="Decennie", y="Listening Time", color_discrete_sequence=["#64D2FF"])
            fig_dec.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#E5E5EA"), xaxis=dict(title=""), yaxis=dict(title="", gridcolor="rgba(255,255,255,0.06)"), margin=dict(l=10, r=10, t=10, b=10), height=280)
            st.plotly_chart(fig_dec, use_container_width=True)

        # Analyse du Zapping (< 30s)
        with ds3:
            st.subheader("⏭️ Artistes les plus zappés")
            if not zaps.empty:
                zap_art = zaps.groupby("Artist")["Listening Time"].count().sort_values(ascending=False).head(5).reset_index()
                zap_art.columns = ["Artiste", "Titres zappés (<30s)"]
                st.dataframe(zap_art, use_container_width=True, hide_index=True)
            else:
                st.info("Aucun titre zappé (< 30s) détecté dans cet historique.")

    # ==========================================
    # ONGLET 3 : MOTEUR DE RECOMMANDATION
    # ==========================================
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("✨ Recommandations Basées sur ton ADN Musical")
        st.caption("Algorithme déterministe : croise tes 5 artistes les plus écoutés avec le graphe de proximité Deezer, en excluant tout ce que tu connais déjà.")

        top_5_ids = (
            ecoutes_valides[ecoutes_valides["artist_id"] > 0]
            .groupby("artist_id")["Listening Time"]
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .index.tolist()
        )
        known_artists = ecoutes_valides["Artist"].str.lower().unique().tolist()

        with st.spinner("Exploration des artistes similaires inédits..."):
            recos = generate_smart_recommendations(top_5_ids, known_artists)

        if recos:
            r_cols = st.columns(4)
            for idx, item in enumerate(recos):
                with r_cols[idx % 4]:
                    st.markdown(f"""
                    <div class="glass-card" style="margin-bottom: 16px;">
                        <div class="card-rank">SUGGESTION #{idx+1}</div>
                        <img src="{item['cover']}" alt="cover">
                        <div class="card-title">{item['track']}</div>
                        <div class="card-sub">{item['artist']} • <i>{item['album']}</i></div>
                    </div>
                    """, unsafe_allow_html=True)
                    if item["preview"]:
                        st.audio(item["preview"], format="audio/mp3")
        else:
            st.warning("Pas assez de données d'artistes identifiés pour générer des suggestions.")

else:
    st.info("👈 Ouvre le menu latéral à gauche pour importer ton fichier Deezer une première fois.")