import streamlit as st
import itertools
import random
import json
import os

# Sayfa Yapılandırması
st.set_page_config(
    page_title="FIFA Kura & Turnuva Yöneticisi",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobil Uyumlu Özel CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 0.8rem;
        padding-right: 0.8rem;
    }
    .match-box {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 10px 12px;
        margin-bottom: 12px;
    }
    .player-label-home {
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .player-label-away {
        color: #f43f5e;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

DATA_FILE = "tournament_state.json"

def save_to_disk():
    state_to_save = {
        "tournament_started": st.session_state.get("tournament_started", False),
        "stage": st.session_state.get("stage", "setup"),
        "all_players_input": st.session_state.get("all_players_input", ""),
        "players_a": st.session_state.get("players_a", []),
        "players_b": st.session_state.get("players_b", []),
        "advancing_count": st.session_state.get("advancing_count", 2),
        "matches_a": st.session_state.get("matches_a", []),
        "matches_b": st.session_state.get("matches_b", []),
        "knockout": st.session_state.get("knockout", {}),
        "draw_done": st.session_state.get("draw_done", False)
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state_to_save, f, ensure_ascii=False, indent=2)

def load_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    st.session_state[k] = v
        except Exception:
            pass

# Fikstür Üretici (Ardışık Maçları Engelleyen Akıllı Sıralama)
def create_balanced_schedule(players, group_name):
    pairs = list(itertools.combinations(players, 2))
    random.shuffle(pairs)
    
    scheduled = []
    remaining = list(pairs)
    last_p1, last_p2 = None, None
    
    while remaining:
        best_candidate = None
        for pair in remaining:
            if pair[0] != last_p1 and pair[0] != last_p2 and pair[1] != last_p1 and pair[1] != last_p2:
                best_candidate = pair
                break
        
        if not best_candidate:
            best_candidate = remaining[0]
            
        scheduled.append(best_candidate)
        remaining.remove(best_candidate)
        last_p1, last_p2 = best_candidate[0], best_candidate[1]
        
    fixtures = []
    for idx, (p1, p2) in enumerate(scheduled):
        fixtures.append({
            "id": f"{group_name}_{idx+1}",
            "group": group_name,
            "home": p1,
            "away": p2,
            "score_home": None,
            "score_away": None,
            "played": False
        })
    return fixtures

# Puan Tablosu Hesaplama
def calculate_standings(players, matches):
    table = {p: {"O": 0, "G": 0, "B": 0, "M": 0, "AG": 0, "YG": 0, "AV": 0, "P": 0} for p in players}
    for m in matches:
        if m["played"] and m["score_home"] is not None and m["score_away"] is not None:
            h, a = m["home"], m["away"]
            sh, sa = int(m["score_home"]), int(m["score_away"])
            
            if h in table and a in table:
                table[h]["O"] += 1
                table[a]["O"] += 1
                table[h]["AG"] += sh
                table[h]["YG"] += sa
                table[a]["AG"] += sa
                table[a]["YG"] += sh
                table[h]["AV"] = table[h]["AG"] - table[h]["YG"]
                table[a]["AV"] = table[a]["AG"] - table[a]["YG"]
                
                if sh > sa:
                    table[h]["G"] += 1
                    table[h]["P"] += 3
                    table[a]["M"] += 1
                elif sa > sh:
                    table[a]["G"] += 1
                    table[a]["P"] += 3
                    table[h]["M"] += 1
                else:
                    table[h]["B"] += 1
                    table[a]["B"] += 1
                    table[h]["P"] += 1
                    table[a]["P"] += 1

    sorted_standings = sorted(
        table.items(),
        key=lambda x: (x[1]["P"], x[1]["AV"], x[1]["AG"]),
        reverse=True
    )
    return sorted_standings

# Oturum Durumunu Yükle
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    load_from_disk()
    if "tournament_started" not in st.session_state:
        st.session_state.tournament_started = False
        st.session_state.stage = "setup"
        st.session_state.draw_done = False

# -------------------------------------------------------------
# 1. KURULUM VE KURA ÇEKİMİ EKRANI
# -------------------------------------------------------------
if not st.session_state.tournament_started or st.session_state.stage == "setup":
    st.title("🎲 FIFA Kura Çekimi & Turnuva Kurulumu")
    
    default_text = st.session_state.get("all_players_input", "Oyuncu 1\nOyuncu 2\nOyuncu 3\nOyuncu 4\nOyuncu 5\nOyuncu 6\nOyuncu 7\nOyuncu 8\nOyuncu 9\nOyuncu 10")
    all_players_raw = st.text_area("📝 Katılımcı Listesi (Her satıra bir oyuncu yazın):", default_text, height=180)
    st.session_state.all_players_input = all_players_raw

    col_opt1, col_opt2 = st.columns([1, 1])
    with col_opt1:
        advancing_count = st.radio(
            "Her gruptan kaç kişi üst tura çıksın?",
            options=[2, 3],
            format_func=lambda x: f"{x} Kişi ({'Direkt Yarı Final: A1-B2 & B1-A2' if x == 2 else 'Liderler Yarı Finale + 2. ve 3.ler Play-off'})",
            index=0 if st.session_state.get("advancing_count", 2) == 2 else 1,
            horizontal=True
        )
        st.session_state.advancing_count = advancing_count

    st.divider()

    if st.button("🎲 Kurayı Çek & Grupları Oluştur", use_container_width=True, type="secondary"):
        player_list = [p.strip() for p in all_players_raw.split("\n") if p.strip()]
        
        min_total = advancing_count * 2
        if len(player_list) < min_total:
            st.error(f"Seçilen kurala göre en az {min_total} oyuncu girmelisiniz!")
        else:
            shuffled = list(player_list)
            random.shuffle(shuffled)
            
            mid = len(shuffled) // 2
            st.session_state.players_a = shuffled[:mid]
            st.session_state.players_b = shuffled[mid:]
            st.session_state.draw_done = True
            save_to_disk()
            st.rerun()

    if st.session_state.get("draw_done", False) and st.session_state.get("players_a") and st.session_state.get("players_b"):
        st.subheader("🎯 Kura Sonuçları")
        c_grp_a, c_grp_b = st.columns(2)
        
        with c_grp_a:
            st.markdown("### 🅰️ A Grubu")
            for idx, p in enumerate(st.session_state.players_a, 1):
                st.markdown(f"**{idx}.** {p}")
                
        with c_grp_b:
            st.markdown("### 🅱️ B Grubu")
            for idx, p in enumerate(st.session_state.players_b, 1):
                st.markdown(f"**{idx}.** {p}")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Turnuvayı & Fikstürü Başlat", use_container_width=True, type="primary"):
            st.session_state.matches_a = create_balanced_schedule(st.session_state.players_a, "A")
            st.session_state.matches_b = create_balanced_schedule(st.session_state.players_b, "B")
            st.session_state.tournament_started = True
            st.session_state.stage = "groups"
            st.session_state.knockout = {}
            save_to_disk()
            st.rerun()

# -------------------------------------------------------------
# 2. GRUP AŞAMASI
# -------------------------------------------------------------
elif st.session_state.stage == "groups":
    st.title("🏆 Grup Karşılaşmaları")
    
    tab_a, tab_b = st.tabs(["🅰️ A Grubu", "🅱️ B Grubu"])
    
    # --- A GRUBU ---
    with tab_a:
        st.subheader("📋 A Grubu Fikstürü")
        for idx, m in enumerate(st.session_state.matches_a):
            st.markdown(f'<div class="match-box"><b>Maç {idx+1}</b>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f'<div class="player-label-home">🏠 {m["home"]}</div>', unsafe_allow_html=True)
                sh_val = m["score_home"] if m["score_home"] is not None else 0
                sh = st.number_input("", min_value=0, max_value=25, value=sh_val, key=f"a_sh_{idx}", label_visibility="collapsed")
                
            with c2:
                st.markdown(f'<div class="player-label-away">✈️ {m["away"]}</div>', unsafe_allow_html=True)
                sa_val = m["score_away"] if m["score_away"] is not None else 0
                sa = st.number_input("", min_value=0, max_value=25, value=sa_val, key=f"a_sa_{idx}", label_visibility="collapsed")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            if m["score_home"] != sh or m["score_away"] != sa:
                m["score_home"] = sh
                m["score_away"] = sa
                m["played"] = True
                save_to_disk()

        st.divider()
        st.subheader("📊 A Grubu Puan Durumu")
        standings_a = calculate_standings(st.session_state.players_a, st.session_state.matches_a)
        table_a_data = []
        for rank, (p, stats) in enumerate(standings_a, 1):
            status = "🟢 Üst Tur" if rank <= st.session_state.advancing_count else "⚪ Elendi"
            table_a_data.append({"Sıra": rank, "Durum": status, "Oyuncu": p, **stats})
        st.dataframe(table_a_data, use_container_width=True, hide_index=True)

    # --- B GRUBU ---
    with tab_b:
        st.subheader("📋 B Grubu Fikstürü")
        for idx, m in enumerate(st.session_state.matches_b):
            st.markdown(f'<div class="match-box"><b>Maç {idx+1}</b>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(f'<div class="player-label-home">🏠 {m["home"]}</div>', unsafe_allow_html=True)
                sh_val = m["score_home"] if m["score_home"] is not None else 0
                sh = st.number_input("", min_value=0, max_value=25, value=sh_val, key=f"b_sh_{idx}", label_visibility="collapsed")
                
            with c2:
                st.markdown(f'<div class="player-label-away">✈️ {m["away"]}</div>', unsafe_allow_html=True)
                sa_val = m["score_away"] if m["score_away"] is not None else 0
                sa = st.number_input("", min_value=0, max_value=25, value=sa_val, key=f"b_sa_{idx}", label_visibility="collapsed")
                
            st.markdown('</div>', unsafe_allow_html=True)
            
            if m["score_home"] != sh or m["score_away"] != sa:
                m["score_home"] = sh
                m["score_away"] = sa
                m["played"] = True
                save_to_disk()

        st.divider()
        st.subheader("📊 B Grubu Puan Durumu")
        standings_b = calculate_standings(st.session_state.players_b, st.session_state.matches_b)
        table_b_data = []
        for rank, (p, stats) in enumerate(standings_b, 1):
            status = "🟢 Üst Tur" if rank <= st.session_state.advancing_count else "⚪ Elendi"
            table_b_data.append({"Sıra": rank, "Durum": status, "Oyuncu": p, **stats})
        st.dataframe(table_b_data, use_container_width=True, hide_index=True)

    st.divider()
    col_act1, col_act2 = st.columns([3, 1])
    with col_act1:
        if st.button("⚔️ Eleme Turlarına Geç", type="primary", use_container_width=True):
            st_a = [p for p, _ in calculate_standings(st.session_state.players_a, st.session_state.matches_a)]
            st_b = [p for p, _ in calculate_standings(st.session_state.players_b, st.session_state.matches_b)]
            adv = st.session_state.advancing_count
            ko = {}
            
            if adv == 2:
                ko["sf1"] = {"home": st_a[0], "away": st_b[1], "sh": 0, "sa": 0, "played": False}
                ko["sf2"] = {"home": st_b[0], "away": st_a[1], "sh": 0, "sa": 0, "played": False}
                ko["final"] = {"home": "SF1 Galibi", "away": "SF2 Galibi", "sh": 0, "sa": 0, "played": False}
                ko["third"] = {"home": "SF1 Mağlubu", "away": "SF2 Mağlubu", "sh": 0, "sa": 0, "played": False}
            elif adv == 3:
                ko["po1"] = {"home": st_a[1], "away": st_b[2], "sh": 0, "sa": 0, "played": False}
                ko["po2"] = {"home": st_b[1], "away": st_a[2], "sh": 0, "sa": 0, "played": False}
                ko["sf1"] = {"home": st_b[0], "away": "PO1 Galibi (A2 vs B3)", "sh": 0, "sa": 0, "played": False}
                ko["sf2"] = {"home": st_a[0], "away": "PO2 Galibi (B2 vs A3)", "sh": 0, "sa": 0, "played": False}
                ko["final"] = {"home": "SF1 Galibi", "away": "SF2 Galibi", "sh": 0, "sa": 0, "played": False}
                ko["third"] = {"home": "SF1 Mağlubu", "away": "SF2 Mağlubu", "sh": 0, "sa": 0, "played": False}
            
            st.session_state.knockout = ko
            st.session_state.stage = "knockout"
            save_to_disk()
            st.rerun()

    with col_act2:
        if st.button("🔄 Sıfırla", use_container_width=True):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()

# -------------------------------------------------------------
# 3. ELEME AŞAMASI (KNOCKOUT)
# -------------------------------------------------------------
elif st.session_state.stage == "knockout":
    st.title("⚔️ Eleme Aşaması & Finaller")
    ko = st.session_state.knockout
    adv = st.session_state.advancing_count

    # Play-off Bölümü (Eğer 3 kişi çıkıyorsa)
    if adv == 3:
        st.subheader("🔥 Play-off (Yarı Final Ön Elemesi)")
        
        # PO 1
        st.markdown('<div class="match-box"><b>Play-off 1 (A2 vs B3)</b>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="player-label-home">🏠 {ko["po1"]["home"]}</div>', unsafe_allow_html=True)
            p1_sh = st.number_input("", min_value=0, max_value=25, value=ko['po1']['sh'], key="po1_h_input", label_visibility="collapsed")
        with c2:
            st.markdown(f'<div class="player-label-away">✈️ {ko["po1"]["away"]}</div>', unsafe_allow_html=True)
            p1_sa = st.number_input("", min_value=0, max_value=25, value=ko['po1']['sa'], key="po1_a_input", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if p1_sh != ko['po1']['sh'] or p1_sa != ko['po1']['sa']:
            ko['po1']['sh'] = p1_sh
            ko['po1']['sa'] = p1_sa
            ko['po1']['played'] = (p1_sh != p1_sa)
            if p1_sh != p1_sa:
                ko['sf1']['away'] = ko['po1']['home'] if p1_sh > p1_sa else ko['po1']['away']
            save_to_disk()
            st.rerun()

        # PO 2
        st.markdown('<div class="match-box"><b>Play-off 2 (B2 vs A3)</b>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="player-label-home">🏠 {ko["po2"]["home"]}</div>', unsafe_allow_html=True)
            p2_sh = st.number_input("", min_value=0, max_value=25, value=ko['po2']['sh'], key="po2_h_input", label_visibility="collapsed")
        with c2:
            st.markdown(f'<div class="player-label-away">✈️ {ko["po2"]["away"]}</div>', unsafe_allow_html=True)
            p2_sa = st.number_input("", min_value=0, max_value=25, value=ko['po2']['sa'], key="po2_a_input", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if p2_sh != ko['po2']['sh'] or p2_sa != ko['po2']['sa']:
            ko['po2']['sh'] = p2_sh
            ko['po2']['sa'] = p2_sa
            ko['po2']['played'] = (p2_sh != p2_sa)
            if p2_sh != p2_sa:
                ko['sf2']['away'] = ko['po2']['home'] if p2_sh > p2_sa else ko['po2']['away']
            save_to_disk()
            st.rerun()
            
        st.divider()

    # Yarı Final Bölümü
    st.subheader("🏅 Yarı Finaller")
    
    # SF 1
    st.markdown('<div class="match-box"><b>Yarı Final 1</b>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="player-label-home">🏠 {ko["sf1"]["home"]}</div>', unsafe_allow_html=True)
        s1_sh = st.number_input("", min_value=0, max_value=25, value=ko['sf1']['sh'], key="sf1_h_input", label_visibility="collapsed")
    with c2:
        st.markdown(f'<div class="player-label-away">✈️ {ko["sf1"]["away"]}</div>', unsafe_allow_html=True)
        s1_sa = st.number_input("", min_value=0, max_value=25, value=ko['sf1']['sa'], key="sf1_a_input", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if s1_sh != ko['sf1']['sh'] or s1_sa != ko['sf1']['sa']:
        ko['sf1']['sh'] = s1_sh
        ko['sf1']['sa'] = s1_sa
        if s1_sh != s1_sa:
            ko['sf1']['played'] = True
            ko['final']['home'] = ko['sf1']['home'] if s1_sh > s1_sa else ko['sf1']['away']
            ko['third']['home'] = ko['sf1']['away'] if s1_sh > s1_sa else ko['sf1']['home']
        save_to_disk()
        st.rerun()

    # SF 2
    st.markdown('<div class="match-box"><b>Yarı Final 2</b>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="player-label-home">🏠 {ko["sf2"]["home"]}</div>', unsafe_allow_html=True)
        s2_sh = st.number_input("", min_value=0, max_value=25, value=ko['sf2']['sh'], key="sf2_h_input", label_visibility="collapsed")
    with c2:
        st.markdown(f'<div class="player-label-away">✈️ {ko["sf2"]["away"]}</div>', unsafe_allow_html=True)
        s2_sa = st.number_input("", min_value=0, max_value=25, value=ko['sf2']['sa'], key="sf2_a_input", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if s2_sh != ko['sf2']['sh'] or s2_sa != ko['sf2']['sa']:
        ko['sf2']['sh'] = s2_sh
        ko['sf2']['sa'] = s2_sa
        if s2_sh != s2_sa:
            ko['sf2']['played'] = True
            ko['final']['away'] = ko['sf2']['home'] if s2_sh > s2_sa else ko['sf2']['away']
            ko['third']['away'] = ko['sf2']['away'] if s2_sh > s2_sa else ko['sf2']['home']
        save_to_disk()
        st.rerun()

    st.divider()

    # Büyük Final ve 3.lük Maçı
    st.subheader("👑 Final Karşılaşmaları")
    
    # Final
    st.markdown('<div class="match-box"><h3>🏆 BÜYÜK FİNAL</h3>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="player-label-home">🏠 {ko["final"]["home"]}</div>', unsafe_allow_html=True)
        f_sh = st.number_input("", min_value=0, max_value=25, value=ko['final']['sh'], key="fin_h_input", label_visibility="collapsed")
    with c2:
        st.markdown(f'<div class="player-label-away">✈️ {ko["final"]["away"]}</div>', unsafe_allow_html=True)
        f_sa = st.number_input("", min_value=0, max_value=25, value=ko['final']['sa'], key="fin_a_input", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if f_sh != ko['final']['sh'] or f_sa != ko['final']['sa']:
        ko['final']['sh'] = f_sh
        ko['final']['sa'] = f_sa
        ko['final']['played'] = (f_sh != f_sa)
        save_to_disk()
        st.rerun()

    if ko['final'].get('played') and ko['final']['sh'] != ko['final']['sa']:
        champ = ko['final']['home'] if ko['final']['sh'] > ko['final']['sa'] else ko['final']['away']
        st.success(f"🎉 **ŞAMPİYON: {champ}** 🎉")

    # 3.lük Maçı
    st.markdown('<div class="match-box"><h3>🥉 3.\'lük Maçı</h3>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="player-label-home">🏠 {ko["third"]["home"]}</div>', unsafe_allow_html=True)
        t_sh = st.number_input("", min_value=0, max_value=25, value=ko['third']['sh'], key="thr_h_input", label_visibility="collapsed")
    with c2:
        st.markdown(f'<div class="player-label-away">✈️ {ko["third"]["away"]}</div>', unsafe_allow_html=True)
        t_sa = st.number_input("", min_value=0, max_value=25, value=ko['third']['sa'], key="thr_a_input", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if t_sh != ko['third']['sh'] or t_sa != ko['third']['sa']:
        ko['third']['sh'] = t_sh
        ko['third']['sa'] = t_sa
        ko['third']['played'] = (t_sh != t_sa)
        save_to_disk()
        st.rerun()

    if ko['third'].get('played') and ko['third']['sh'] != ko['third']['sa']:
        runner_up = ko['third']['home'] if ko['third']['sh'] > ko['third']['sa'] else ko['third']['away']
        st.info(f"🥉 **Turnuva 3.'sü: {runner_up}**")

    st.divider()
    col_nav1, col_nav2 = st.columns([3, 1])
    with col_nav1:
        if st.button("⬅️ Grup Karşılaşmalarına Dön", use_container_width=True):
            st.session_state.stage = "groups"
            save_to_disk()
            st.rerun()
    with col_nav2:
        if st.button("🔄 Yeni Turnuva Başlat", use_container_width=True):
            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            st.session_state.clear()
            st.rerun()
