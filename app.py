import streamlit as st
import pandas as pd
from riot_connector import fetch_player_stats

# Configuration de la page Streamlit
st.set_page_config(page_title="LoL Stat Tracker", layout="wide", initial_sidebar_state="expanded")

st.title("📈 LoL Performance Tracker")
st.markdown("Suivez vos points forts et axes d'amélioration sur vos champions préférés.")

# --- BARRE LATÉRALE (Configuration) ---
st.sidebar.header("🔑 Connexion API & Profil")
api_key = st.sidebar.text_input("Clé API Riot (RGAPI-...)", type="password")
st.sidebar.caption("Récupère ta clé sur [developer.riotgames.com](https://developer.riotgames.com/)")

st.sidebar.markdown("---")
game_name = st.sidebar.text_input("Pseudo en jeu", value="Faker")
tag_line = st.sidebar.text_input("Tagline (sans le #)", value="EUW")
region = st.sidebar.selectbox("Région", ["euw1", "eun1", "na1"], index=0)
match_count = st.sidebar.slider("Nombre de matchs à analyser", 5, 30, 15)

# --- LOGIQUE PRINCIPALE ---
if st.sidebar.button("🚀 Lancer l'analyse"):
    if not api_key:
        st.error("Veuillez renseigner votre clé API Riot dans la barre latérale.")
    else:
        with st.spinner(f"Récupération des données pour {game_name}#{tag_line}..."):
            try:
                # On force la suppression des anciennes stats de la session pour éviter les mélanges
                if 'df_stats' in st.session_state:
                    del st.session_state['df_stats']
                
                # Appel du script de connexion
                df = fetch_player_stats(api_key, game_name, tag_line, region, match_count)
                
                if df.empty:
                    st.warning("Aucune partie de classée récente (Solo/Duo) trouvée pour ce joueur.")
                else:
                    st.session_state['df_stats'] = df
                    # On stocke aussi le nom du joueur analysé pour vérification
                    st.session_state['current_player'] = f"{game_name}#{tag_line}"
                    st.success(f"Données de {game_name} chargées avec succès !")
            except Exception as e:
                st.error(str(e))

st.markdown("---")

# --- AFFICHAGE DES RÉSULTATS ---
if 'df_stats' in st.session_state:
    df = st.session_state['df_stats']
    st.info(f"📊 Analyse des données actuellement chargées pour : **{st.session_state.get('current_player', 'Inconnu')}**")
    
    # Filtre par champion
    champions_disponibles = sorted(df['Champion'].unique())
    
    col_select, _ = st.columns([2, 2])
    with col_select:
        champion_selectionne = st.selectbox("🎯 Choisis le champion à analyser :", champions_disponibles)
    
    # Filtrage du tableau de données pour le champion choisi
    df_champ = df[df['Champion'] == champion_selectionne].reset_index(drop=True)
    
    if df_champ.empty:
        st.warning(f"Aucune partie trouvée avec {champion_selectionne} dans l'échantillon analysé.")
    else:
        # Calcul des moyennes globales du champion
        winrate = round((df_champ['Victoire'].sum() / len(df_champ)) * 100, 1)
        avg_cs = round(df_champ['CS_Min'].mean(), 2)
        avg_kp = round(df_champ['KP_Pourcent'].mean(), 1)
        
        # Affichage des KPIs sous forme de tuiles (Metrics)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Parties Jouées", len(df_champ))
        col2.metric("Winrate", f"{winrate}%")
        col3.metric("Moyenne CS/Min", avg_cs)
        col4.metric("Participation Kills", f"{avg_kp}%")
        
        st.markdown("---")
        
        # --- GRAPHIQUES SPÉCIFIQUES AUX RÔLES ---
        # Détection automatique du rôle (Jungle ou Top)
        role_principal = df_champ['Rôle'].mode()[0] if not df_champ['Rôle'].empty else "UNKNOWN"
        
        col_graph1, col_graph2 = st.columns(2)
        
        with col_graph1:
            st.subheader("📈 Évolution du CS/Min par match")
            # Utilisation de l'index + 1 pour afficher "Match 1, Match 2..." au lieu des IDs cryptiques de Riot
            df_chart_cs = df_champ[['CS_Min']].copy()
            df_chart_cs.index = df_chart_cs.index + 1
            st.line_chart(df_chart_cs)
            
        with col_graph2:
            # Affichage personnalisé selon le champion (Yorick vs Junglers)
            if champion_selectionne == "Yorick" or role_principal == "TOP":
                st.subheader("🧱 Focus Toplane : Dégâts aux Bâtiments")
                df_chart_dmg = df_champ[['Dégâts_Bâtiments']].copy()
                df_chart_dmg.index = df_chart_dmg.index + 1
                st.bar_chart(df_chart_dmg)
                st.caption("Votre objectif en split-push (Yorick) est de maximiser cette barre à chaque partie.")
                
            elif champion_selectionne == "Amumu":
                st.subheader("💤 Focus Amumu : Temps de CC total (sec)")
                df_chart_cc = df_champ[['Temps_CC_Infligé']].copy()
                df_chart_cc.index = df_chart_cc.index + 1
                st.bar_chart(df_chart_cc)
                st.caption("Mesure l'efficacité de vos bandelettes et de vos ultimes en combat.")
                
            else: # Kha'Zix, Ambessa ou autre Jungler
                st.subheader("⚔️ Focus Jungle : Dégâts infligés aux Champions")
                df_chart_champ = df_champ[['Dégâts_Champions']].copy()
                df_chart_champ.index = df_chart_champ.index + 1
                st.bar_chart(df_chart_champ)
                st.caption("Mesure votre agressivité et votre impact dans les escarmouches.")

        # --- HISTORIQUE BRUT ---
        st.subheader("📋 Tableau détaillé des parties (Vérification)")
        df_affichage = df_champ[['Champion', 'Victoire', 'Kills', 'Deaths', 'Assists', 'CS_Min', 'KP_Pourcent']].copy()
        # Remplacement des True/False par Victoire/Défaite pour que ça soit plus propre
        df_affichage['Victoire'] = df_affichage['Victoire'].map({True: 'Victoire', False: 'Défaite'})
        st.dataframe(df_affichage, use_container_width=True)
else:
    st.info("💡 Entrez vos identifiants à gauche et cliquez sur 'Lancer l'analyse' pour charger vos statistiques.")