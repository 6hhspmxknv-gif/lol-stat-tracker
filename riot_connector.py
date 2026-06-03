import pandas as pd
from riotwatcher import RiotWatcher, LolWatcher, ApiError

def fetch_player_stats(api_key, game_name, tag_line, region="euw1", match_count=10):
    """
    Récupère les derniers matchs d'un joueur et extrait les KPIs pour le Jungle/Top.
    """
    account_watcher = RiotWatcher(api_key)
    lol_watcher = LolWatcher(api_key)
    
    try:
        # Détermination de la zone géographique continentale
        geo_region = "europe" if region in ["euw1", "eun1", "tr1", "ru"] else "americas"
        
        # 1. Récupération du compte via RiotWatcher
        account = account_watcher.account.by_riot_id(geo_region, game_name, tag_line)
        puuid = account['puuid']
        
        # 2. CORRECTION : Utilisation de matchlist_by_puuid pour Match-V5
        match_ids = lol_watcher.match.matchlist_by_puuid(geo_region, puuid, queue=420, count=match_count)
        
        if not match_ids:
            return pd.DataFrame()
            
        stats_list = []
        
        # 3. Boucle sur chaque match pour extraire les données
        for match_id in match_ids:
            match_detail = lol_watcher.match.by_id(geo_region, match_id)
            
            game_duration_min = match_detail['info']['gameDuration'] / 60
            
            for participant in match_detail['info']['participants']:
                if participant['puuid'] == puuid:
                    
                    total_cs = participant['totalMinionsKilled'] + participant['neutralMinionsKilled']
                    cs_min = total_cs / game_duration_min if game_duration_min > 0 else 0
                    
                    team_id = participant['teamId']
                    team_kills = sum(p['kills'] for p in match_detail['info']['participants'] if p['teamId'] == team_id)
                    kp = ((participant['kills'] + participant['assists']) / team_kills) * 100 if team_kills > 0 else 0
                    
                    stats_list.append({
                        'Match_ID': match_id,
                        'Champion': participant['championName'],
                        'Rôle': participant['teamPosition'],
                        'Victoire': participant['win'],
                        'Kills': participant['kills'],
                        'Deaths': participant['deaths'],
                        'Assists': participant['assists'],
                        'CS_Min': round(cs_min, 2),
                        'KP_Pourcent': round(kp, 1),
                        'Dégâts_Bâtiments': participant['damageDealtToBuildings'],
                        'Dégâts_Champions': participant['totalDamageDealtToChampions'],
                        'Temps_CC_Infligé': participant['totalTimeCCDealt']
                    })
                    
        return pd.DataFrame(stats_list)

    except ApiError as e:
        if e.response.status_code == 403:
            raise Exception("Clé API Riot expirée ou invalide. Génère une nouvelle clé.")
        elif e.response.status_code == 404:
            raise Exception("Joueur introuvable. Vérifie le pseudo et le tag.")
        else:
            raise Exception(f"Erreur API Riot: {e.response.status_code}")