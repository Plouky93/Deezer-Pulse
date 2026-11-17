import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import sqlite3
import time
import os
import base64

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Deezer Pulse • Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- PALETTES DE THÈMES PERSONNALISABLES ---
THEMES = {
    "💜 Pulse Néon (OLED Original)": {
        "name": "Pulse Néon",
        "bg_gradient": """
            radial-gradient(circle at 12% 10%, rgba(120, 40, 200, 0.28) 0%, transparent 40%),
            radial-gradient(circle at 88% 20%, rgba(235, 50, 120, 0.22) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(20, 110, 245, 0.20) 0%, transparent 48%)
        """,
        "primary": "#FF375F",
        "secondary": "#BF5AF2",
        "accent": "#5E5CE6",
        "card_hover": "rgba(255, 55, 95, 0.55)",
        "chart_scale": ["#5E5CE6", "#BF5AF2", "#FF375F"],
        "chart_line": "#FF375F",
        "heatmap_scale": ["#0A0A0C", "#3A1C71", "#D76D77", "#FFAF7B"],
        "donut_colors": ["#FF375F", "#BF5AF2", "#5E5CE6", "#64D2FF"]
    },
    "💚 Émeraude Cyber (Deezer / Spotify)": {
        "name": "Émeraude Cyber",
        "bg_gradient": """
            radial-gradient(circle at 12% 10%, rgba(48, 209, 88, 0.26) 0%, transparent 40%),
            radial-gradient(circle at 88% 20%, rgba(0, 245, 160, 0.20) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(10, 132, 255, 0.18) 0%, transparent 48%)
        """,
        "primary": "#30D158",
        "secondary": "#00F5A0",
        "accent": "#0A84FF",
        "card_hover": "rgba(48, 209, 88, 0.55)",
        "chart_scale": ["#0A84FF", "#00F5A0", "#30D158"],
        "chart_line": "#30D158",
        "heatmap_scale": ["#0A0A0C", "#0B3C2A", "#10B981", "#6EE7B7"],
        "donut_colors": ["#30D158", "#00F5A0", "#0A84FF", "#FFD60A"]
    },
    "🔥 Sunset Glow (Ambre & Corail)": {
        "name": "Sunset Glow",
        "bg_gradient": """
            radial-gradient(circle at 12% 10%, rgba(255, 55, 95, 0.28) 0%, transparent 40%),
            radial-gradient(circle at 88% 20%, rgba(255, 159, 10, 0.24) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(255, 214, 10, 0.16) 0%, transparent 48%)
        """,
        "primary": "#FF9F0A",
        "secondary": "#FF375F",
        "accent": "#FFD60A",
        "card_hover": "rgba(255, 159, 10, 0.55)",
        "chart_scale": ["#7A003C", "#FF375F", "#FF9F0A", "#FFD60A"],
        "chart_line": "#FF9F0A",
        "heatmap_scale": ["#0A0A0C", "#5C1D24", "#C84B31", "#FFD60A"],
        "donut_colors": ["#FF9F0A", "#FF375F", "#FFD60A", "#BF5AF2"]
    },
    "💎 Titane Arctique (Ice White & Cyan)": {
        "name": "Titane Arctique",
        "bg_gradient": """
            radial-gradient(circle at 12% 10%, rgba(100, 210, 255, 0.25) 0%, transparent 40%),
            radial-gradient(circle at 88% 20%, rgba(10, 132, 255, 0.22) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(255, 255, 255, 0.12) 0%, transparent 48%)
        """,
        "primary": "#64D2FF",
        "secondary": "#0A84FF",
        "accent": "#E5E5EA",
        "card_hover": "rgba(100, 210, 255, 0.55)",
        "chart_scale": ["#1C3144", "#0A84FF", "#64D2FF"],
        "chart_line": "#64D2FF",
        "heatmap_scale": ["#0A0A0C", "#0D324D", "#1E6091", "#64D2FF"],
        "donut_colors": ["#64D2FF", "#0A84FF", "#BF5AF2", "#E5E5EA"]
    },
    "🔮 Saphir Profond (Midnight Abyss)": {
        "name": "Saphir Profond",
        "bg_gradient": """
            radial-gradient(circle at 12% 10%, rgba(10, 132, 255, 0.28) 0%, transparent 40%),
            radial-gradient(circle at 88% 20%, rgba(94, 92, 230, 0.24) 0%, transparent 42%),
            radial-gradient(circle at 50% 90%, rgba(191, 90, 242, 0.18) 0%, transparent 48%)
        """,
        "primary": "#0A84FF",
        "secondary": "#5E5CE6",
        "accent": "#BF5AF2",
        "card_hover": "rgba(10, 132, 255, 0.55)",
        "chart_scale": ["#061E47", "#0A84FF", "#5E5CE6", "#BF5AF2"],
        "chart_line": "#0A84FF",
        "heatmap_scale": ["#050814", "#12255A", "#2553B8", "#72A5FF"],
        "donut_colors": ["#0A84FF", "#5E5CE6", "#BF5AF2", "#64D2FF"]
    }
}

# --- GESTION DU THÈME VISUEL DANS LA SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎨 Personnalisation & Thème")
    theme_choice = st.selectbox(
        "Palette d'ambiance :",
        options=list(THEMES.keys()),
        index=0,
        key="app_theme_selection"
    )
    current_theme = THEMES[theme_choice]

# --- INJECTION CSS DYNAMIQUE (GLASSMORPHISM & COULEURS DU THÈME) ---
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
    }}

    .stApp {{
        background-color: #000000;
        background-image: {current_theme['bg_gradient']};
        background-attachment: fixed;
        color: #F5F5F7;
    }}

    header[data-testid="stHeader"] {{ background: transparent; }}

    section[data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 13, 0.90);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(25px);
    }}

    /* Cartes KPI Glassmorphism */
    div[data-testid="stMetric"] {{
        background: rgba(22, 22, 26, 0.55);
        backdrop-filter: blur(22px);
        -webkit-backdrop-filter: blur(22px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 18px 22px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.16);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
    }}

    div[data-testid="stMetric"]:hover {{
        transform: translateY(-3px);
        border-color: {current_theme['card_hover']};
        box-shadow: 0 12px 35px rgba(0, 0, 0, 0.75);
    }}

    div[data-testid="stMetricLabel"] {{
        color: #98989D !important;
        font-size: 0.78rem !important;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }}

    div[data-testid="stMetricValue"] {{
        color: #FFFFFF !important;
        font-size: 1.95rem !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}

    /* Cartes Glassmorphism Universelles */
    .glass-card {{
        background: rgba(24, 24, 29, 0.62);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 20px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
        transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}
    .glass-card:hover {{
        transform: translateY(-4px);
        border-color: {current_theme['card_hover']};
        box-shadow: 0 14px 40px rgba(0, 0, 0, 0.8);
    }}
    .glass-card img {{
        border-radius: 14px;
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        box-shadow: 0 8px 24px rgba(0,0,0,0.6);
        margin-bottom: 12px;
    }}
    .card-rank {{
        font-size: 0.75rem;
        font-weight: 700;
        color: {current_theme['primary']};
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .card-title {{
        font-size: 1.05rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 4px 0 2px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .card-sub {{
        font-size: 0.85rem;
        color: #A1A1A6;
        margin-bottom: 6px;
    }}

    /* Badges & Pills */
    .pulse-pill {{
        display: inline-block;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 30px;
        padding: 4px 12px;
        font-size: 0.78rem;
        font-weight: 600;
        color: {current_theme['secondary']};
        margin: 3px 2px;
    }}

    /* Vitrine Showcase sur Landing Page */
    .showcase-card {{
        background: rgba(20, 20, 25, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 22px;
        padding: 22px;
        backdrop-filter: blur(20px);
        transition: all 0.3s ease;
        text-align: left;
        margin-bottom: 16px;
    }}
    .showcase-card:hover {{
        border-color: {current_theme['primary']};
        transform: translateY(-3px);
        background: rgba(26, 26, 33, 0.75);
    }}
    .showcase-icon {{
        font-size: 1.8rem;
        margin-bottom: 8px;
    }}
    .showcase-title {{
        font-size: 1.2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 6px;
    }}
    .showcase-desc {{
        font-size: 0.88rem;
        color: #98989D;
        line-height: 1.45;
    }}

    /* Hero Banner */
    .hero-banner {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 24px;
        padding: 34px 28px;
        text-align: center;
        backdrop-filter: blur(25px);
        margin-bottom: 28px;
    }}

    /* Archétype Card */
    .archetype-container {{
        background: linear-gradient(145deg, rgba(30, 30, 38, 0.75) 0%, rgba(15, 15, 20, 0.85) 100%);
        border: 1px solid {current_theme['card_hover']};
        border-radius: 24px;
        padding: 26px;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.7);
    }}

    /* Onglets stylisés */
    button[data-baseweb="tab"] {{
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #A1A1A6 !important;
        transition: color 0.2s ease !important;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {current_theme['primary']} !important;
        border-bottom-color: {current_theme['primary']} !important;
    }}

    h1 {{
        background: linear-gradient(135deg, #FFFFFF 0%, #A1A1A6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
    }}

    div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"] {{
        background: rgba(18, 18, 22, 0.52);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 20px;
        padding: 15px;
    }}

    /* Boutons Primaires & Accents */
    div.stButton > button {{
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 100%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 14px;
        color: #FFFFFF;
        font-weight: 600;
        transition: all 0.25s ease;
    }}
    div.stButton > button:hover {{
        border-color: {current_theme['primary']};
        color: #FFFFFF;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
    }}
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
        res = requests.get("https://api.deezer.com/search", params={"q": query, "limit": 1}, timeout=3).json()
        if res.get("data"):
            item = res["data"][0]
            track_id = item["id"]
            artist_id = item.get("artist", {}).get("id", 0)
            cover_url = item.get("album", {}).get("cover_xl") or item.get("album", {}).get("cover_big") or item.get("album", {}).get("cover_medium") or ""
            
            details = requests.get(f"https://api.deezer.com/track/{track_id}", timeout=3).json()
            bpm = details.get("bpm", 0)
            release_date = details.get("release_date", "Inconnue")
            rank = details.get("rank", 0)

            cursor.execute(
                "INSERT OR REPLACE INTO tracks_meta VALUES (?, ?, ?, ?, ?, ?, ?)",
                (artist, title, bpm, release_date, rank, cover_url, artist_id)
            )
            conn.commit()
            time.sleep(0.04)
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
            rel_res = requests.get(f"https://api.deezer.com/artist/{aid}/related", params={"limit": 6}, timeout=4).json()
            for rel_artist in rel_res.get("data", []):
                r_name = rel_artist.get("name", "")
                r_id = rel_artist.get("id")
                if r_name.lower() in seen_artists:
                    continue
                seen_artists.add(r_name.lower())

                top_tracks = requests.get(f"https://api.deezer.com/artist/{r_id}/top", params={"limit": 1}, timeout=4).json()
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
                time.sleep(0.05)
        except Exception:
            continue
    return recos[:8]

# --- CALCUL DE L'ARCHÉTYPE MUSICAL & TRAITS DE CARACTÈRE ---
def calculate_musical_archetype(ecoutes_valides, zaps, uniques):
    total_valides = len(ecoutes_valides)
    total_zaps = len(zaps)
    total_tous = total_valides + total_zaps
    if total_tous == 0 or total_valides == 0:
        return None

    pct_nuit = (ecoutes_valides["Heure"].isin([22, 23, 0, 1, 2, 3, 4, 5]).sum() / total_valides) * 100
    pct_matin = (ecoutes_valides["Heure"].isin([6, 7, 8, 9, 10]).sum() / total_valides) * 100
    pct_zap = (total_zaps / total_tous) * 100
    ratio_fidelite = total_valides / max(1, len(uniques))
    
    bpm_valides = ecoutes_valides[ecoutes_valides["bpm"] > 0]["bpm"]
    mean_bpm = bpm_valides.mean() if not bpm_valides.empty else 115

    annees = ecoutes_valides["Annee"].dropna()
    mean_year = annees.mean() if not annees.empty else 2022

    # Détermination de l'archétype principal
    if pct_nuit >= 35:
        name = "L'Oiseau de Nuit"
        icon = "🌙"
        tagline = "Créature Nocturne & Sonore"
        desc = "Plus du tiers de vos écoutes se déroulent après 22h. C'est quand la ville s'endort que vos sessions musicales prennent vie."
        badges = ["#Noctambule", "#StudioDeMinuit", "#ÉcouteIntimiste"]
    elif pct_zap >= 30:
        name = "Le Zappeur Frénétique"
        icon = "⚡"
        tagline = "Exigence & Vitesse Décisionnelle"
        desc = "Vous accordez 10 secondes maximum à un titre pour faire ses preuves. Si la flamme ne prend pas immédiatement, vous passez au suivant !"
        badges = ["#NextImmédiat", "#HyperSélectif", "#Instinctif"]
    elif ratio_fidelite >= 2.8:
        name = "Le Puriste Monomaniaque"
        icon = "💿"
        tagline = "Fidélité Absolue & Boucles Obsessionnelles"
        desc = "Quand vous découvrez un morceau ou un album coup de cœur, vous l'écoutez jusqu'à l'usure complète. Vos classiques restent gravés."
        badges = ["#EnBoucle", "#LoyautéAbsolue", "#AlbumEnEntier"]
    elif mean_year < 2005:
        name = "L'Archiviste Vintage"
        icon = "📻"
        tagline = "Nostalgie & Pépites Intemporelles"
        desc = "Votre univers puise dans les décennies passées. Les productions d'hier ont pour vous une authenticité que le présent peine à égaler."
        badges = ["#ÂmeVintage", "#Classiques", "#Intemporel"]
    elif mean_bpm >= 126:
        name = "Le Sprinter Rythmique"
        icon = "🔥"
        tagline = "Haute Fréquence & Adrénaline"
        desc = "Votre tempo moyen est ultra vigoureux. Vous avez besoin d'énergie, de kicks percutants et de pulsations rapides pour carburer."
        badges = ["#HighBPM", "#TurboDrive", "#PleinÉnergie"]
    else:
        name = "L'Explorateur Caméléon"
        icon = "🧭"
        tagline = "Curiosité Tout-Terrain"
        desc = "Vous refusez les étiquettes : de l'urbain au rock, du rétro à la modernité, votre palette musicale est aussi diverse que raffinée."
        badges = ["#Éclectique", "#CuriositéTotale", "#OpenMinded"]

    # Scores normalisés (0 à 100) pour le Radar Chart
    score_nocturne = min(100, int(pct_nuit * 2.2))
    score_fidelite = min(100, int(ratio_fidelite * 28))
    score_tempo = min(100, max(15, int((mean_bpm - 70) * (100 / 90))))
    score_vintage = min(100, max(15, int((2026 - mean_year) * 3.5)))
    score_patience = min(100, max(10, int(100 - pct_zap)))

    return {
        "name": name,
        "icon": icon,
        "tagline": tagline,
        "desc": desc,
        "badges": badges,
        "stats": {
            "pct_nuit": pct_nuit,
            "pct_matin": pct_matin,
            "pct_zap": pct_zap,
            "ratio_fidelite": ratio_fidelite,
            "mean_bpm": mean_bpm,
            "mean_year": mean_year
        },
        "radar": {
            "Nocturnité": score_nocturne,
            "Loyauté d'écoute": score_fidelite,
            "Tempo & Énergie": score_tempo,
            "Âme Vintage": score_vintage,
            "Patience (Anti-Zap)": score_patience
        }
    }

# --- CHARGEMENT / SAUVEGARDE LOCALE DES DONNÉES ---
SAVE_FILE = "saved_history.pkl"
DEMO_FILE = "deezer_test_complet.csv"

# Sidebar : Gestion des sources et réinitialisation
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📂 Source des Données")
    
    sidebar_upload = st.file_uploader(
        "Remplacer l'historique (CSV / XLSX)",
        type=["csv", "xlsx"],
        key="sidebar_uploader"
    )
    
    if os.path.exists(SAVE_FILE):
        st.success("Données en mémoire actives")
        if st.button("🗑️ Déconnecter & Effacer", use_container_width=True):
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            for k in list(st.session_state.keys()):
                if k not in ["app_theme_selection", "tabs_arrangement"]:
                    del st.session_state[k]
            st.rerun()

# Vérification du fichier chargé
df_raw = None
if sidebar_upload is not None:
    if sidebar_upload.name.endswith(".csv"):
        df_raw = pd.read_csv(sidebar_upload)
    else:
        xl = pd.ExcelFile(sidebar_upload)
        sheet = "10_listeningHistory" if "10_listeningHistory" in xl.sheet_names else xl.sheet_names[0]
        df_raw = pd.read_excel(sidebar_upload, sheet_name=sheet)
    df_raw.to_pickle(SAVE_FILE)
    st.rerun()
elif os.path.exists(SAVE_FILE):
    try:
        df_raw = pd.read_pickle(SAVE_FILE)
    except Exception:
        os.remove(SAVE_FILE)
        df_raw = None

# --- EN-TÊTE PRINCIPAL ---
header_col1, header_col2 = st.columns([3, 1])
with header_col1:
    st.title("Deezer Pulse")
    st.caption("STUDIO ANALYTIQUE • ARCHÉTYPES MUSICAUX • DÉCOUVERTES OLED")
with header_col2:
    st.markdown("<div style='text-align: right; padding-top: 15px;'><span class='pulse-pill'>✦ Édition Studio 2026</span></div>", unsafe_allow_html=True)

# =========================================================================
# ÉTAT 1 : AUCUNE DONNÉE CHARGÉE -> PAGE D'ACCUEIL SHOWCASE & DÉMO
# =========================================================================
if df_raw is None:
    st.markdown(f"""
    <div class="hero-banner">
        <div style="font-size: 2.8rem; margin-bottom: 8px;">✦</div>
        <h2 style="font-size: 2.1rem; font-weight: 800; margin-bottom: 10px; color: #FFFFFF;">
            Découvrez votre véritable empreinte musicale
        </h2>
        <p style="font-size: 1.05rem; color: #A1A1A6; max-width: 680px; margin: 0 auto 20px auto; line-height: 1.5;">
            Importez votre historique Deezer pour révéler votre archétype sonore, analyser vos rythmes biologiques d'écoute et explorer des recommandations inédites.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Actions principales : Démo immédiate ou Upload central
    action_col1, action_col2 = st.columns(2)
    with action_col1:
        st.markdown(f"""
        <div class="glass-card" style="text-align: left; padding: 24px; min-height: 220px;">
            <div style="font-size: 1.6rem; margin-bottom: 6px;">⚡</div>
            <h3 style="color: #FFFFFF; font-size: 1.25rem; margin-bottom: 6px;">Tester en 1 Clic (Mode Démo)</h3>
            <p style="color: #A1A1A6; font-size: 0.88rem; line-height: 1.45; margin-bottom: 16px;">
                Explorez immédiatement toutes les fonctionnalités de l'application grâce à un profil complet d'exemple (180 écoutes réelles).
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Charger le Profil Démo", use_container_width=True, type="primary"):
            if os.path.exists(DEMO_FILE):
                demo_df = pd.read_csv(DEMO_FILE)
            elif os.path.exists("mock_data.csv"):
                demo_df = pd.read_csv("mock_data.csv")
            else:
                demo_df = pd.DataFrame()
            demo_df.to_pickle(SAVE_FILE)
            st.rerun()

    with action_col2:
        st.markdown(f"""
        <div class="glass-card" style="text-align: left; padding: 24px; min-height: 220px;">
            <div style="font-size: 1.6rem; margin-bottom: 6px;">📂</div>
            <h3 style="color: #FFFFFF; font-size: 1.25rem; margin-bottom: 6px;">Importer votre Fichier Deezer</h3>
            <p style="color: #A1A1A6; font-size: 0.88rem; line-height: 1.45; margin-bottom: 8px;">
                Glissez votre fichier d'export Deezer (format CSV ou Excel XLSX). Vos données restent 100% locales sur votre machine.
            </p>
        </div>
        """, unsafe_allow_html=True)
        landing_upload = st.file_uploader(
            "Glissez votre fichier ici :",
            type=["csv", "xlsx"],
            key="landing_uploader",
            label_visibility="collapsed"
        )
        if landing_upload is not None:
            if landing_upload.name.endswith(".csv"):
                df_loaded = pd.read_csv(landing_upload)
            else:
                xl = pd.ExcelFile(landing_upload)
                sheet = "10_listeningHistory" if "10_listeningHistory" in xl.sheet_names else xl.sheet_names[0]
                df_loaded = pd.read_excel(landing_upload, sheet_name=sheet)
            df_loaded.to_pickle(SAVE_FILE)
            st.rerun()

    # Guide pas-à-pas pour l'export Deezer
    with st.expander("📖 Comment récupérer mon historique officiel Deezer en 3 étapes ?"):
        st.markdown("""
        1. **Accédez aux paramètres de votre compte** sur [Deezer.com](https://www.deezer.com) depuis votre navigateur.
        2. Allez dans la section **« Gestion des données personnelles »** ou **« Télécharger mes données »**.
        3. Deezer génère une archive contenant votre historique complet (`10_listeningHistory`). Il suffit de glisser le fichier CSV ou XLSX ici !
        """)

    # Aperçu / Vitrine des Onglets du Dashboard
    st.markdown("<br><h3 style='text-align: center; margin-bottom: 20px;'>✦ Aperçu de ce que le Studio vous réserve</h3>", unsafe_allow_html=True)
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f"""
        <div class="showcase-card">
            <div class="showcase-icon">📊</div>
            <div class="showcase-title">Vue d'ensemble & Podium</div>
            <div class="showcase-desc">
                Calcul précis des heures réelles d'écoute, indice de fidélité, tempo moyen et <b>Podium 3D en pochettes HD</b> de vos albums cultes.
            </div>
            <div style="margin-top: 14px;">
                <span class="pulse-pill">Podium HD</span>
                <span class="pulse-pill">Top Artistes</span>
                <span class="pulse-pill">Rythme Circadien</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""
        <div class="showcase-card">
            <div class="showcase-icon">🧬</div>
            <div class="showcase-title">ADN & Archétype Sonore</div>
            <div class="showcase-desc">
                Découvrez votre personnalité musicale (<i>L'Oiseau de Nuit, Le Zappeur Frénétique, Le Puriste...</i>) avec votre <b>Radar 5 dimensions</b>.
            </div>
            <div style="margin-top: 14px;">
                <span class="pulse-pill">Profil Psychologique</span>
                <span class="pulse-pill">Radar Sonore</span>
                <span class="pulse-pill">Humeurs</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""
        <div class="showcase-card">
            <div class="showcase-icon">🔬</div>
            <div class="showcase-title">Data Science & Comportement</div>
            <div class="showcase-desc">
                Visualisez votre <b>Heatmap 24h × 7 jours</b>, la répartition de vos décennies musicales et la détection impitoyable de votre zapping.
            </div>
            <div style="margin-top: 14px;">
                <span class="pulse-pill">Heatmap 24h/7j</span>
                <span class="pulse-pill">Zapping &lt; 30s</span>
                <span class="pulse-pill">Supports</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    sc4, sc5 = st.columns(2)
    with sc4:
        st.markdown(f"""
        <div class="showcase-card">
            <div class="showcase-icon">✨</div>
            <div class="showcase-title">Découvertes Sur-Mesure</div>
            <div class="showcase-desc">
                Algorithme croisant vos favoris avec le graphe de proximité Deezer pour dénicher des pépites inédites avec <b>extraits audio 30s intégrés</b>.
            </div>
            <div style="margin-top: 14px;">
                <span class="pulse-pill">Lecteur Audio 30s</span>
                <span class="pulse-pill">Artistes Similaires</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with sc5:
        st.markdown(f"""
        <div class="showcase-card">
            <div class="showcase-icon">📸</div>
            <div class="showcase-title">Mon Deezer Wrapped</div>
            <div class="showcase-desc">
                Votre bilan musical condensé dans une carte visuelle haut de gamme prête à être capturée et partagée sur vos réseaux sociaux.
            </div>
            <div style="margin-top: 14px;">
                <span class="pulse-pill">Story Instagram</span>
                <span class="pulse-pill">Export Autonome</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# =========================================================================
# ÉTAT 2 : DONNÉES DISPONIBLES -> DASHBOARD COMPLET & PERSONNALISABLE
# =========================================================================
else:
    # 1. Normalisation & Enrichissement des métadonnées
    df = df_raw.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Heure"] = df["Date"].dt.hour
    df["Jour_Num"] = df["Date"].dt.dayofweek
    jours_fr = {0: "Lun", 1: "Mar", 2: "Mer", 3: "Jeu", 4: "Ven", 5: "Sam", 6: "Dim"}
    df["Jour"] = df["Jour_Num"].map(jours_fr)

    # Récupération / Synchronisation des métadonnées SQLite
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute("SELECT artist, title FROM tracks_meta")
    already_cached = set(cursor.fetchall())
    
    uniques_all = df[["Artist", "Song Title", "Album"]].drop_duplicates(subset=["Artist", "Song Title"])
    missing_items = [r for _, r in uniques_all.iterrows() if (r["Artist"], r["Song Title"]) not in already_cached]
    
    if len(missing_items) > 0:
        pbar = st.progress(0, text=f"Synchronisation de {len(missing_items)} morceaux avec l'API Deezer...")
        for idx, row in enumerate(missing_items):
            get_deezer_metadata(row["Artist"], row["Song Title"], row.get("Album", ""), conn)
            pbar.progress((idx + 1) / len(missing_items))
        pbar.empty()

    # Lecture rapide de toutes les métadonnées depuis le cache
    meta_cache = {}
    cursor.execute("SELECT artist, title, bpm, release_date, rank, cover_url, artist_id FROM tracks_meta")
    for r in cursor.fetchall():
        meta_cache[(r[0], r[1])] = {
            "bpm": r[2], "release_date": r[3], "rank": r[4], "cover_url": r[5], "artist_id": r[6]
        }
    conn.close()

    # Enrichissement instantané du DataFrame
    df["bpm"] = df.apply(lambda r: meta_cache.get((r["Artist"], r["Song Title"]), {}).get("bpm", 0), axis=1)
    df["release_date"] = df.apply(lambda r: meta_cache.get((r["Artist"], r["Song Title"]), {}).get("release_date", "Inconnue"), axis=1)
    df["cover_url"] = df.apply(lambda r: meta_cache.get((r["Artist"], r["Song Title"]), {}).get("cover_url", ""), axis=1)
    df["artist_id"] = df.apply(lambda r: meta_cache.get((r["Artist"], r["Song Title"]), {}).get("artist_id", 0), axis=1)
    df["Annee"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year

    # 2. FILTRE TEMPOREL DYNAMIQUE
    st.markdown("<br>", unsafe_allow_html=True)
    filter_col1, filter_col2, filter_col3 = st.columns([2, 3, 2])
    
    with filter_col1:
        time_filter_mode = st.selectbox(
            "⏳ Période d'analyse :",
            ["Tout l'historique", "Cette Année", "30 derniers jours", "Période personnalisée"],
            key="time_filter_select"
        )

    df_filtered = df.copy()
    if time_filter_mode == "Cette Année":
        annee_active = df["Date"].dt.year.max()
        df_filtered = df[df["Date"].dt.year == annee_active]
    elif time_filter_mode == "30 derniers jours":
        date_max = df["Date"].max()
        df_filtered = df[df["Date"] >= (date_max - pd.Timedelta(days=30))]
    elif time_filter_mode == "Période personnalisée":
        with filter_col2:
            d_min = df["Date"].min().date()
            d_max = df["Date"].max().date()
            picked_range = st.date_input(
                "Sélectionnez les dates :",
                [d_min, d_max],
                min_value=d_min,
                max_value=d_max
            )
            if len(picked_range) == 2:
                df_filtered = df[(df["Date"].dt.date >= picked_range[0]) & (df["Date"].dt.date <= picked_range[1])]

    with filter_col3:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 26px; color: #98989D; font-size: 0.85rem;">
            <b>{len(df_filtered)}</b> écoutes actives analysées
        </div>
        """, unsafe_allow_html=True)

    if df_filtered.empty:
        st.warning("Aucune écoute trouvée pour la période sélectionnée.")
        st.stop()

    ecoutes_valides = df_filtered[df_filtered["Listening Time"] >= 30].copy()
    zaps = df_filtered[df_filtered["Listening Time"] < 30].copy()
    uniques = ecoutes_valides[["Artist", "Song Title", "Album"]].drop_duplicates(subset=["Artist", "Song Title"])

    # Calcul de l'archétype
    archetype_data = calculate_musical_archetype(ecoutes_valides, zaps, uniques)

    # 3. GESTION DE L'AGENCEMENT DES ONGLETS DANS LA SIDEBAR
    ALL_AVAILABLE_TABS = [
        "📊 Vue d'ensemble",
        "🧬 ADN & Archétype",
        "🔬 Data Science & Comportement",
        "✨ Découvertes Sur-Mesure",
        "📸 Mon Deezer Wrapped"
    ]

    with st.sidebar:
        st.markdown("### 📑 Agencement des Onglets")
        st.caption("Personnalisez l'ordre et le contenu affiché :")
        active_tabs_order = st.multiselect(
            "Onglets actifs :",
            options=ALL_AVAILABLE_TABS,
            default=ALL_AVAILABLE_TABS,
            key="tabs_arrangement"
        )
        if not active_tabs_order:
            active_tabs_order = ALL_AVAILABLE_TABS

    # Création dynamique des onglets selon l'ordre choisi par l'utilisateur
    st.markdown("<br>", unsafe_allow_html=True)
    tabs_instances = st.tabs(active_tabs_order)

    # Rendu dynamique de chaque onglet
    for tab_title, tab_content in zip(active_tabs_order, tabs_instances):
        with tab_content:
            st.markdown("<br>", unsafe_allow_html=True)

            # ==========================================
            # ONGLET : 📊 VUE D'ENSEMBLE
            # ==========================================
            if tab_title == "📊 Vue d'ensemble":
                # KPIs principaux
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

                # Graphiques : Top Artistes & Rythme Circadien
                st.markdown("<br>", unsafe_allow_html=True)
                g1, g2 = st.columns(2)
                with g1:
                    st.subheader("Top Artistes (Minutes)")
                    top_art = (ecoutes_valides.groupby("Artist")["Listening Time"].sum().sort_values(ascending=True).tail(8) / 60).reset_index()
                    fig_art = px.bar(
                        top_art,
                        x="Listening Time",
                        y="Artist",
                        orientation="h",
                        color="Listening Time",
                        color_continuous_scale=current_theme["chart_scale"]
                    )
                    fig_art.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#E5E5EA"),
                        coloraxis_showscale=False,
                        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=""),
                        yaxis=dict(showgrid=False, title=""),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=310
                    )
                    st.plotly_chart(fig_art, use_container_width=True)

                with g2:
                    st.subheader("Rythme Circadien (Écoutes / Heure)")
                    heures_completes = pd.DataFrame({"Heure": range(24)})
                    par_heure = ecoutes_valides.groupby("Heure")["Listening Time"].count().reset_index()
                    par_heure = heures_completes.merge(par_heure, on="Heure", how="left").fillna(0)
                    
                    fig_heure = go.Figure(go.Scatter(
                        x=par_heure["Heure"],
                        y=par_heure["Listening Time"],
                        mode="lines+markers",
                        line=dict(color=current_theme["chart_line"], width=3, shape="spline"),
                        marker=dict(size=6, color="#FFFFFF", line=dict(width=2, color=current_theme["chart_line"])),
                        fill="tozeroy",
                        fillcolor=f"{current_theme['chart_line']}26"
                    ))
                    fig_heure.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#E5E5EA"),
                        xaxis=dict(showgrid=False, tickmode="linear", dtick=3, title="", ticksuffix="h"),
                        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", title=""),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=310
                    )
                    st.plotly_chart(fig_heure, use_container_width=True)

                # Classement des Titres
                st.subheader("Classement des Titres")
                top_titres = (
                    ecoutes_valides.groupby(["Artist", "Song Title", "Album", "bpm", "release_date"], as_index=False)
                    .agg(Écoutes=("Listening Time", "count"), Minutes=("Listening Time", lambda x: round(x.sum() / 60, 1)))
                    .sort_values(by=["Minutes", "Écoutes"], ascending=False)
                )
                st.dataframe(top_titres, use_container_width=True, hide_index=True)

            # ==========================================
            # ONGLET : 🧬 ADN & ARCHÉTYPE MUSICAL
            # ==========================================
            elif tab_title == "🧬 ADN & Archétype":
                if archetype_data:
                    arch_col1, arch_col2 = st.columns([1, 1])
                    
                    with arch_col1:
                        badge_html = "".join([f"<span class='pulse-pill'>{b}</span>" for b in archetype_data['badges']])
                        st.markdown(f"""
                        <div class="archetype-container">
                            <div style="font-size: 2.8rem; margin-bottom: 8px;">{archetype_data['icon']}</div>
                            <div class="card-rank">{archetype_data['tagline']}</div>
                            <h2 style="color: #FFFFFF; font-size: 1.9rem; font-weight: 800; margin: 6px 0 12px 0;">
                                {archetype_data['name']}
                            </h2>
                            <p style="color: #C7C7CC; font-size: 0.95rem; line-height: 1.55; margin-bottom: 20px;">
                                {archetype_data['desc']}
                            </p>
                            <div>{badge_html}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Métriques comportementales détaillées
                        st.markdown("<br>", unsafe_allow_html=True)
                        m1, m2, m3 = st.columns(3)
                        m1.metric("Écoutes de nuit", f"{archetype_data['stats']['pct_nuit']:.1f}%", "22h - 06h")
                        m2.metric("Taux de zap", f"{archetype_data['stats']['pct_zap']:.1f}%", "< 30s")
                        m3.metric("Fidélité titre", f"{archetype_data['stats']['ratio_fidelite']:.1f}x", "écoutes moy.")

                    with arch_col2:
                        st.subheader("🕸️ Radar de votre Empreinte Sonore")
                        st.caption("Modélisation multidimensionnelle de vos habitudes d'écoute (score 0 à 100)")
                        
                        radar_keys = list(archetype_data["radar"].keys())
                        radar_values = list(archetype_data["radar"].values())
                        
                        fig_radar = go.Figure()
                        fig_radar.add_trace(go.Scatterpolar(
                            r=radar_values + [radar_values[0]],
                            theta=radar_keys + [radar_keys[0]],
                            fill='toself',
                            fillcolor=f"{current_theme['primary']}30",
                            line=dict(color=current_theme['primary'], width=3),
                            marker=dict(color=current_theme['secondary'], size=7)
                        ))
                        fig_radar.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100],
                                    showticklabels=False,
                                    linecolor="rgba(255,255,255,0.12)",
                                    gridcolor="rgba(255,255,255,0.08)"
                                ),
                                angularaxis=dict(
                                    linecolor="rgba(255,255,255,0.12)",
                                    gridcolor="rgba(255,255,255,0.08)",
                                    color="#E5E5EA"
                                )
                            ),
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            showlegend=False,
                            margin=dict(l=35, r=35, t=25, b=25),
                            height=330
                        )
                        st.plotly_chart(fig_radar, use_container_width=True)

                    # Horloge des 4 Humeurs de la Journée
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader("🕒 Répartition des 4 Humeurs de la Journée")
                    
                    def classify_period(h):
                        if 6 <= h < 12:
                            return "Matin Énergique (06h - 12h)"
                        elif 12 <= h < 18:
                            return "Après-Midi Focus (12h - 18h)"
                        elif 18 <= h < 23:
                            return "Soirée Décompression (18h - 23h)"
                        else:
                            return "Nuit Éthérée (23h - 06h)"
                            
                    ecoutes_valides["Periode"] = ecoutes_valides["Heure"].apply(classify_period)
                    periode_df = ecoutes_valides.groupby("Periode")["Listening Time"].count().reset_index()
                    periode_df.columns = ["Période", "Nombre d'écoutes"]
                    
                    fig_humeur = px.bar(
                        periode_df,
                        x="Période",
                        y="Nombre d'écoutes",
                        color="Nombre d'écoutes",
                        color_continuous_scale=current_theme["chart_scale"]
                    )
                    fig_humeur.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#E5E5EA"),
                        coloraxis_showscale=False,
                        xaxis=dict(title=""),
                        yaxis=dict(title="", gridcolor="rgba(255,255,255,0.06)"),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=260
                    )
                    st.plotly_chart(fig_humeur, use_container_width=True)

            # ==========================================
            # ONGLET : 🔬 DATA SCIENCE & COMPORTEMENT
            # ==========================================
            elif tab_title == "🔬 Data Science & Comportement":
                st.subheader("🌡️ Empreinte Temporelle (Jour × Heure)")
                st.caption("Visualisez la matrice de densité de vos sessions musicales à travers les jours de la semaine.")
                ordre_jours = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                pivot_heat = ecoutes_valides.pivot_table(index="Jour", columns="Heure", values="Listening Time", aggfunc="count", fill_value=0)
                pivot_heat = pivot_heat.reindex(index=ordre_jours, columns=range(24), fill_value=0)

                fig_heat = px.imshow(
                    pivot_heat,
                    labels=dict(x="Heure", y="Jour", color="Écoutes"),
                    x=[f"{h}h" for h in range(24)],
                    y=ordre_jours,
                    color_continuous_scale=current_theme["heatmap_scale"],
                    aspect="auto"
                )
                fig_heat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#E5E5EA"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=280
                )
                st.plotly_chart(fig_heat, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                ds1, ds2, ds3 = st.columns(3)

                with ds1:
                    st.subheader("📱 Supports d'écoute")
                    if "Platform" in ecoutes_valides.columns:
                        plat_df = ecoutes_valides.groupby("Platform")["Listening Time"].sum().reset_index()
                        fig_plat = px.pie(
                            plat_df,
                            values="Listening Time",
                            names="Platform",
                            hole=0.62,
                            color_discrete_sequence=current_theme["donut_colors"]
                        )
                        fig_plat.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#E5E5EA"),
                            margin=dict(l=10, r=10, t=10, b=10),
                            height=280,
                            showlegend=True
                        )
                        st.plotly_chart(fig_plat, use_container_width=True)

                with ds2:
                    st.subheader("⏳ Décennies Musicales")
                    ecoutes_valides["Decennie"] = (ecoutes_valides["Annee"] // 10 * 10).dropna().astype(int).astype(str) + "s"
                    dec_df = ecoutes_valides[ecoutes_valides["Decennie"] != "nans"].groupby("Decennie")["Listening Time"].count().reset_index()
                    fig_dec = px.bar(dec_df, x="Decennie", y="Listening Time", color_discrete_sequence=[current_theme["primary"]])
                    fig_dec.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#E5E5EA"),
                        xaxis=dict(title=""),
                        yaxis=dict(title="", gridcolor="rgba(255,255,255,0.06)"),
                        margin=dict(l=10, r=10, t=10, b=10),
                        height=280
                    )
                    st.plotly_chart(fig_dec, use_container_width=True)

                with ds3:
                    st.subheader("⏭️ Artistes les plus zappés")
                    if not zaps.empty:
                        zap_art = zaps.groupby("Artist")["Listening Time"].count().sort_values(ascending=False).head(5).reset_index()
                        zap_art.columns = ["Artiste", "Titres zappés (<30s)"]
                        st.dataframe(zap_art, use_container_width=True, hide_index=True)
                    else:
                        st.info("Aucun titre zappé (< 30s) détecté dans cet historique.")

            # ==========================================
            # ONGLET : ✨ DÉCOUVERTES SUR-MESURE
            # ==========================================
            elif tab_title == "✨ Découvertes Sur-Mesure":
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

            # ==========================================
            # ONGLET : 📸 MON DEEZER WRAPPED
            # ==========================================
            elif tab_title == "📸 Mon Deezer Wrapped":
                st.subheader("📸 Votre Carte Deezer Pulse Wrapped")
                st.caption("Un récapitulatif ultra-visuel façon Story Instagram prêt à être partagé.")

                # Calcul des éléments phares pour la carte
                top_art_name = ecoutes_valides.groupby("Artist")["Listening Time"].sum().idxmax() if not ecoutes_valides.empty else "Artiste Inconnu"
                top_track_row = ecoutes_valides.groupby(["Song Title", "Artist"])["Listening Time"].sum().idxmax() if not ecoutes_valides.empty else ("Titre", "Artiste")
                top_album_row = ecoutes_valides.groupby(["Album", "cover_url"])["Listening Time"].sum().idxmax() if not ecoutes_valides.empty else ("Album", "")
                
                wrapped_cover = top_album_row[1] if top_album_row[1] else "https://e-cdns-images.dzcdn.net/images/cover/d41d8cd98f00b204e9800998ecf8427e/500x500-000000-80-0-0.jpg"
                total_hours_w = ecoutes_valides["Listening Time"].sum() / 3600
                arch_name_w = archetype_data['name'] if archetype_data else 'Mélomane'
                arch_icon_w = archetype_data['icon'] if archetype_data else '✦'

                w_col1, w_col2 = st.columns([1, 1])
                with w_col1:
                    # Affichage HTML de la Story Card
                    wrapped_html = f"""
                    <div style="
                        background: radial-gradient(circle at 50% 20%, rgba(30, 30, 42, 0.95), rgba(10, 10, 15, 0.98));
                        border: 2px solid {current_theme['primary']};
                        border-radius: 28px;
                        padding: 30px;
                        max-width: 440px;
                        margin: 0 auto;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.85);
                        text-align: center;
                        font-family: -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
                    ">
                        <div style="font-size: 0.8rem; font-weight: 700; color: {current_theme['primary']}; letter-spacing: 0.12em; text-transform: uppercase;">
                            ✦ DEEZER PULSE WRAPPED ✦
                        </div>
                        <div style="font-size: 2.2rem; margin: 10px 0 2px 0;">{arch_icon_w}</div>
                        <div style="font-size: 1.45rem; font-weight: 800; color: #FFFFFF; margin-bottom: 4px;">
                            {arch_name_w}
                        </div>
                        <div style="font-size: 0.82rem; color: #8E8E93; margin-bottom: 20px;">
                            PROFIL PSYCHOLOGIQUE D'ÉCOUTE
                        </div>
                        
                        <img src="{wrapped_cover}" style="
                            width: 220px;
                            height: 220px;
                            border-radius: 18px;
                            box-shadow: 0 12px 30px rgba(0,0,0,0.7);
                            margin-bottom: 18px;
                            object-fit: cover;
                        ">
                        
                        <div style="background: rgba(255,255,255,0.06); border-radius: 18px; padding: 14px; margin-bottom: 18px; text-align: left;">
                            <div style="font-size: 0.75rem; color: #8E8E93; text-transform: uppercase;">Top Morceau</div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {top_track_row[0]}
                            </div>
                            <div style="font-size: 0.85rem; color: {current_theme['secondary']};">{top_track_row[1]}</div>
                        </div>

                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 20px;">
                            <div style="background: rgba(255,255,255,0.04); border-radius: 14px; padding: 10px; text-align: center;">
                                <div style="font-size: 0.7rem; color: #8E8E93;">TEMPS D'ÉCOUTE</div>
                                <div style="font-size: 1.25rem; font-weight: 700; color: #FFFFFF;">{total_hours_w:.1f} h</div>
                            </div>
                            <div style="background: rgba(255,255,255,0.04); border-radius: 14px; padding: 10px; text-align: center;">
                                <div style="font-size: 0.7rem; color: #8E8E93;">TOP ARTISTE</div>
                                <div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{top_art_name}</div>
                            </div>
                        </div>

                        <div style="font-size: 0.72rem; color: #636366; letter-spacing: 0.05em;">
                            GÉNÉRÉ PAR DEEZER PULSE STUDIO • ÉDITION OLED
                        </div>
                    </div>
                    """
                    st.markdown(wrapped_html, unsafe_allow_html=True)

                with w_col2:
                    st.markdown("### 📤 Partager votre Bilan")
                    st.write("Téléchargez votre Story Card au format HTML autonome (prête à ouvrir en plein écran et à capturer) ou copiez le récapitulatif pour les réseaux sociaux.")
                    
                    # Téléchargement HTML autonome
                    standalone_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mon Deezer Pulse Wrapped</title>
</head>
<body style="background: #000; margin: 0; padding: 40px; display: flex; justify-content: center; align-items: center; min-height: 100vh;">
    {wrapped_html}
</body>
</html>"""
                    st.download_button(
                        label="📥 Télécharger ma Story Card (HTML)",
                        data=standalone_html,
                        file_name="deezer_pulse_wrapped.html",
                        mime="text/html",
                        use_container_width=True
                    )

                    # Texte à copier pour Twitter / Instagram / Discord
                    recap_text = f"""✦ MON DEEZER PULSE WRAPPED ✦
🧬 Archétype : {arch_icon_w} {arch_name_w}
⏱️ Temps d'écoute : {total_hours_w:.1f} heures
👑 Artiste N°1 : {top_art_name}
🎵 Morceau fétiche : {top_track_row[0]} ({top_track_row[1]})
💿 Album coup de cœur : {top_album_row[0]}
Généré avec Deezer Pulse Studio"""

                    st.text_area("Texte pour vos réseaux sociaux :", recap_text, height=180)
