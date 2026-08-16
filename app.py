import streamlit as st
import itertools
import random

st.set_page_config(page_title="FIFA Turnuva Yöneticisi", page_icon="⚽", layout="wide")

# --- YARDIMCI FONKSİYONLAR ---
def create_group_fixtures(players, group_name):
    matches = list(itertools.combinations(players, 2))
    random.shuffle(matches)
    fixture_list = []
    for idx, (p1, p2) in enumerate(matches):
        fixture_list.append({
            "id": f"{group_name}_{idx+1}",
            "group": group_name,
            "home": p1,
            "away": p2,
            "score_home": None,
            "score_away": None,
            "played": False
        })
    return fixture_list

def calculate_standings(players, matches):
    table = {p: {"O": 0, "G": 0, "B": 0, "M": 0, "AG": 0, "YG": 0, "AV": 0, "P": 0} for p in players}
    for m in matches:
        if m["played"] and m["score_home"] is not None and m["score_away"] is not None:
            h, a = m["home"], m["away"]
            sh, sa = m["score_home"], m["score_away"]
            
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

# --- SESSION STATE BAŞLATMA ---
if "tournament_started" not in st.session_state:
    st.session_state.tournament_started = False
if "stage" not in st.session_state:
    st.session_state.stage = "groups"  # 'groups' veya 'knockout'

# --- 1. KURULUM EKRANI ---
if not st.session_state.tournament_started:
    st.title("⚽ FIFA Turnuva Kurulumu")
    
    col1, col2 = st.columns(2)
    with col1:
        group_a_raw = st.text_area("A Grubu Oyuncuları (Her satıra bir isim)", "Oyuncu 1\nOyuncu 2\nOyuncu 3\nOyuncu 4\nOyuncu 5", height=130)
    with col2:
        group_b_raw = st.text_area("B Grubu Oyuncuları (Her satıra bir isim)", "Oyuncu 6\nOyuncu 7\nOyuncu 8\nOyuncu 9\nOyuncu 10", height=130)
    
    advancing_count = st.radio(
        "Her gruptan kaç kişi üst tura çıksın?",
        options=[2, 3],
        format_func=lambda x: f"{x} Kişi ({'Doğrudan Yarı Final' if x == 2 else 'Grup 1.leri Bay + Play-off / Yarı Final'})",
        horizontal=True
    )

    if st.button("Turnuvayı Başlat 🚀", use_container_width=True, type="primary"):
        players_a = [p.strip() for p in group_a_raw.split("\n") if p.strip()]
        players_b = [p.strip() for p in group_b_raw.split("\n") if p.strip()]
        
        if len(players_a) < 2 or len(players_b) < 2:
            st.error("Her grupta en az 2 oyuncu olmalıdır.")
        elif advancing_count == 3 and (len(players_a) < 3 or len(players_b) < 3):
            st.error("3 kişi çıkabilmesi için her grupta en az 3 oyuncu olmalıdır.")
        else:
            st.session_state.players_a = players_a
            st.session_state.players_b = players_b
            st.session_state.advancing_count = advancing_count
            st.session_state.matches_a = create_group_fixtures(players_a, "A")
            st.session_state.matches_b = create_group_fixtures(players_b, "B")
            st.session_state.tournament_started = True
            st.session_state.stage = "groups"
            st.session_state.knockout = {}
            st.rerun()

# --- 2. GRUP AŞAMASI ---
elif st.session_state.stage == "groups":
    st.title("🏆 Grup Aşaması")

    tab1, tab2 = st.tabs(["🅰️ A Grubu", "🅱️ B Grubu"])
    
    with tab1:
        st.subheader("A Grubu Fikstür & Skorlar")
        for m in st.session_state.matches_a:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 3])
            c1.markdown(f"**{m['home']}**")
            sh = c2.number_input("", min_value=0, max_value=20, value=m["score_home"] if m["played"] else 0, key=f"sh_{m['id']}")
            sa = c3.number_input("", min_value=0, max_value=20, value=m["score_away"] if m["played"] else 0, key=f"sa_{m['id']}")
            c4.markdown(f"**{m['away']}**")
            if not m["played"] and (sh != 0 or sa != 0):
                m["score_home"] = sh
                m["score_away"] = sa
                m["played"] = True
            elif m["played"]:
                m["score_home"] = sh
                m["score_away"] = sa

        st.divider()
        st.subheader("📊 A Grubu Puan Durumu")
        standings_a = calculate_standings(st.session_state.players_a, st.session_state.matches_a)
        st.dataframe(
            [{"Sıra": idx+1, "Oyuncu": p, **stats} for idx, (p, stats) in enumerate(standings_a)],
            use_container_width=True,
            hide_index=True
        )

    with tab2:
        st.subheader("B Grubu Fikstür & Skorlar")
        for m in st.session_state.matches_b:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 3])
            c1.markdown(f"**{m['home']}**")
            sh = c2.number_input("", min_value=0, max_value=20, value=m["score_home"] if m["played"] else 0, key=f"sh_{m['id']}")
            sa = c3.number_input("", min_value=0, max_value=20, value=m["score_away"] if m["played"] else 0, key=f"sa_{m['id']}")
            c4.markdown(f"**{m['away']}**")
            if not m["played"] and (sh != 0 or sa != 0):
                m["score_home"] = sh
                m["score_away"] = sa
                m["played"] = True
            elif m["played"]:
                m["score_home"] = sh
                m["score_away"] = sa

        st.divider()
        st.subheader("📊 B Grubu Puan Durumu")
        standings_b = calculate_standings(st.session_state.players_b, st.session_state.matches_b)
        st.dataframe(
            [{"Sıra": idx+1, "Oyuncu": p, **stats} for idx, (p, stats) in enumerate(standings_b)],
            use_container_width=True,
            hide_index=True
        )

    all_played = all(m["played"] for m in st.session_state.matches_a + st.session_state.matches_b)
    st.divider()
    
    c_btn1, c_btn2 = st.columns([3, 1])
    with c_btn1:
        if st.button("Eleme Aşamasına Geç ⚔️", type="primary", use_container_width=True):
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
                ko["sf1"] = {"home": st_b[0], "away": "PO1 Galibi (A2/B3)", "sh": 0, "sa": 0, "played": False}
                ko["sf2"] = {"home": st_a[0], "away": "PO2 Galibi (B2/A3)", "sh": 0, "sa": 0, "played": False}
                ko["final"] = {"home": "SF1 Galibi", "away": "SF2 Galibi", "sh": 0, "sa": 0, "played": False}
                ko["third"] = {"home": "SF1 Mağlubu", "away": "SF2 Mağlubu", "sh": 0, "sa": 0, "played": False}

            st.session_state.knockout = ko
            st.session_state.stage = "knockout"
            st.rerun()

    with c_btn2:
        if st.button("Turnuvayı Sıfırla 🔄", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- 3. ELEME AŞAMASI (KNOCKOUT) ---
elif st.session_state.stage == "knockout":
    st.title("⚔️ Eleme Turları")
    ko = st.session_state.knockout
    adv = st.session_state.advancing_count

    # Play-off (Eğer 3 kişi çıkıyorsa)
    if adv == 3:
        st.subheader("🔥 Play-off / Yarı Final Ön Elemesi")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**PO 1:** {ko['po1']['home']} vs {ko['po1']['away']}")
            c_h, c_a = st.columns(2)
            ko['po1']['sh'] = c_h.number_input("Skor 1", min_value=0, max_value=20, value=ko['po1']['sh'], key="po1_h")
            ko['po1']['sa'] = c_a.number_input("Skor 2", min_value=0, max_value=20, value=ko['po1']['sa'], key="po1_a")
            if ko['po1']['sh'] != ko['po1']['sa']:
                ko['po1']['played'] = True
                ko['sf1']['away'] = ko['po1']['home'] if ko['po1']['sh'] > ko['po1']['sa'] else ko['po1']['away']

        with col2:
            st.markdown(f"**PO 2:** {ko['po2']['home']} vs {ko['po2']['away']}")
            c_h, c_a = st.columns(2)
            ko['po2']['sh'] = c_h.number_input("Skor 1", min_value=0, max_value=20, value=ko['po2']['sh'], key="po2_h")
            ko['po2']['sa'] = c_a.number_input("Skor 2", min_value=0, max_value=20, value=ko['po2']['sa'], key="po2_a")
            if ko['po2']['sh'] != ko['po2']['sa']:
                ko['po2']['played'] = True
                ko['sf2']['away'] = ko['po2']['home'] if ko['po2']['sh'] > ko['po2']['sa'] else ko['po2']['away']
        st.divider()

    # Yarı Final
    st.subheader("🏅 Yarı Final")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Yarı Final 1:** {ko['sf1']['home']} vs {ko['sf1']['away']}")
        c_h, c_a = st.columns(2)
        ko['sf1']['sh'] = c_h.number_input("Skor 1", min_value=0, max_value=20, value=ko['sf1']['sh'], key="sf1_h")
        ko['sf1']['sa'] = c_a.number_input("Skor 2", min_value=0, max_value=20, value=ko['sf1']['sa'], key="sf1_a")
        if ko['sf1']['sh'] != ko['sf1']['sa']:
            ko['sf1']['played'] = True
            w1 = ko['sf1']['home'] if ko['sf1']['sh'] > ko['sf1']['sa'] else ko['sf1']['away']
            l1 = ko['sf1']['away'] if ko['sf1']['sh'] > ko['sf1']['sa'] else ko['sf1']['home']
            ko['final']['home'] = w1
            ko['third']['home'] = l1

    with col2:
        st.markdown(f"**Yarı Final 2:** {ko['sf2']['home']} vs {ko['sf2']['away']}")
        c_h, c_a = st.columns(2)
        ko['sf2']['sh'] = c_h.number_input("Skor 1", min_value=0, max_value=20, value=ko['sf2']['sh'], key="sf2_h")
        ko['sf2']['sa'] = c_a.number_input("Skor 2", min_value=0, max_value=20, value=ko['sf2']['sa'], key="sf2_a")
        if ko['sf2']['sh'] != ko['sf2']['sa']:
            ko['sf2']['played'] = True
            w2 = ko['sf2']['home'] if ko['sf2']['sh'] > ko['sf2']['sa'] else ko['sf2']['away']
            l2 = ko['sf2']['away'] if ko['sf2']['sh'] > ko['sf2']['sa'] else ko['sf2']['home']
            ko['final']['away'] = w2
            ko['third']['away'] = l2
    
    st.divider()

    # Final & 3.'lük Maçı
    st.subheader("👑 Final & 🥉 3.'lük Maçı")
    col_fin, col_thr = st.columns(2)
    with col_fin:
        st.markdown(f"### 🏆 BÜYÜK FİNAL\n**{ko['final']['home']}** vs **{ko['final']['away']}**")
        c_h, c_a = st.columns(2)
        ko['final']['sh'] = c_h.number_input("Final Skor 1", min_value=0, max_value=20, value=ko['final']['sh'], key="fin_h")
        ko['final']['sa'] = c_a.number_input("Final Skor 2", min_value=0, max_value=20, value=ko['final']['sa'], key="fin_a")
        if ko['final']['sh'] != ko['final']['sa']:
            champion = ko['final']['home'] if ko['final']['sh'] > ko['final']['sa'] else ko['final']['away']
            st.success(f"🎉 **ŞAMPİYON: {champion}** 🎉")

    with col_thr:
        st.markdown(f"### 🥉 3.'lük Karşılaşması\n**{ko['third']['home']}** vs **{ko['third']['away']}**")
        c_h, c_a = st.columns(2)
        ko['third']['sh'] = c_h.number_input("3.lük Skor 1", min_value=0, max_value=20, value=ko['third']['sh'], key="thr_h")
        ko['third']['sa'] = c_a.number_input("3.lük Skor 2", min_value=0, max_value=20, value=ko['third']['sa'], key="thr_a")
        if ko['third']['sh'] != ko['third']['sa']:
            third_place = ko['third']['home'] if ko['third']['sh'] > ko['third']['sa'] else ko['third']['away']
            st.info(f"🥉 **Turnuva 3.'sü: {third_place}**")

    st.divider()
    c_b1, c_b2 = st.columns(2)
    with c_b1:
        if st.button("⬅️ Gruplara Geri Dön", use_container_width=True):
            st.session_state.stage = "groups"
            st.rerun()
    with c_b2:
        if st.button("Turnuvayı Sıfırla 🔄", use_container_width=True):
            st.session_state.clear()
            st.rerun()
