import streamlit as st
import random
import math
import pandas as pd

st.set_page_config(page_title="Turnuva Yönetim Sistemi", layout="centered")

st.title("🏆 Turnuva Yönetim Sistemi")

# Session State (Hafıza Yönetimi)
if 'oyuncular' not in st.session_state:
    st.session_state.oyuncular = []
if 'gA' not in st.session_state:
    st.session_state.gA = []
if 'gB' not in st.session_state:
    st.session_state.gB = []
if 'maclarA' not in st.session_state:
    st.session_state.maclarA = []
if 'maclarB' not in st.session_state:
    st.session_state.maclarB = []
if 'skorlarA' not in st.session_state:
    st.session_state.skorlarA = {}
if 'skorlarB' not in st.session_state:
    st.session_state.skorlarB = {}

tab1, tab2, tab3 = st.tabs(["🎲 Kura & Oyuncular", "⚽ Grup Maçları & Puan", "🏆 Yarı Final"])

# --- TAB 1: KURA ÇEKİMİ ---
with tab1:
    st.subheader("Oyuncu Listesi")
    raw_input = st.text_area("Oyuncu İsimleri (Her satıra bir isim)", value="KOFİ\nABT\nAVNİ\nTOPCU\nAPO\nAZMİ\nFURKAN\nDURMUŞ", height=200)
    
    col1, col2 = st.columns(2)
    if col1.button("🎲 KURA ÇEK", type="primary", use_container_width=True):
        oyuncular = [x.strip() for x in raw_input.split('\n') if x.strip()]
        if len(oyuncular) < 4:
            st.error("En az 4 oyuncu giriniz!")
        else:
            random.shuffle(oyuncular)
            st.session_state.oyuncular = oyuncular
            
            # Gruplara Dağıt
            yari = math.ceil(len(oyuncular) / 2)
            st.session_state.gA = oyuncular[:yari]
            st.session_state.gB = oyuncular[yari:]
            
            # Akıllı Maç Oluşturucu
            def akilli_maclar(grup):
                maclar = []
                for i in range(len(grup)):
                    for j in range(i+1, len(grup)):
                        maclar.append((grup[i], grup[j]))
                random.shuffle(maclar)
                return maclar
            
            st.session_state.maclarA = akilli_maclar(st.session_state.gA)
            st.session_state.maclarB = akilli_maclar(st.session_state.gB)
            st.session_state.skorlarA = {}
            st.session_state.skorlarB = {}
            st.success("Kura çekildi! Grup maçları oluşturuldu.")

    if col2.button("🗑️ Turnuvayı Sıfırla", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    if st.session_state.gA:
        c1, c2 = st.columns(2)
        with c1:
            st.write("### A Grubu")
            for p in st.session_state.gA:
                st.info(p)
        with c2:
            st.write("### B Grubu")
            for p in st.session_state.gB:
                st.warning(p)

# --- TAB 2: MAÇLAR VE PUAN DURUMU ---
with tab2:
    if not st.session_state.maclarA:
        st.info("Lütfen önce Kura Çekin.")
    else:
        st.subheader("⚽ A Grubu Maçları")
        for idx, (p1, p2) in enumerate(st.session_state.maclarA):
            col_m, col_s1, col_s2 = st.columns([2, 1, 1])
            col_m.write(f"**{p1}** vs **{p2}**")
            s1 = col_s1.number_input(f"{p1}", min_value=0, max_value=20, key=f"a_{idx}_1", value=st.session_state.skorlarA.get(f"{idx}_1", 0))
            s2 = col_s2.number_input(f"{p2}", min_value=0, max_value=20, key=f"a_{idx}_2", value=st.session_state.skorlarA.get(f"{idx}_2", 0))
            st.session_state.skorlarA[f"{idx}_1"] = s1
            st.session_state.skorlarA[f"{idx}_2"] = s2

        st.divider()
        st.subheader("⚽ B Grubu Maçları")
        for idx, (p1, p2) in enumerate(st.session_state.maclarB):
            col_m, col_s1, col_s2 = st.columns([2, 1, 1])
            col_m.write(f"**{p1}** vs **{p2}**")
            s1 = col_s1.number_input(f"{p1}", min_value=0, max_value=20, key=f"b_{idx}_1", value=st.session_state.skorlarB.get(f"{idx}_1", 0))
            s2 = col_s2.number_input(f"{p2}", min_value=0, max_value=20, key=f"b_{idx}_2", value=st.session_state.skorlarB.get(f"{idx}_2", 0))
            st.session_state.skorlarB[f"{idx}_1"] = s1
            st.session_state.skorlarB[f"{idx}_2"] = s2

        # Puan Durumu Hesaplama Fonksiyonu
        def hesapla_puan(grup, maclar, skorlar, prefix):
            stats = {p: {'O': 0, 'G': 0, 'B': 0, 'M': 0, 'AG': 0, 'YG': 0, 'AV': 0, 'Puan': 0} for p in grup}
            for idx, (p1, p2) in enumerate(maclar):
                s1 = skorlar.get(f"{idx}_1", 0)
                s2 = skorlar.get(f"{idx}_2", 0)
                
                # Sadece skor girildiyse (Varsayılan 0-0'ı maç oynandı saymamak için kontrol eklenebilir)
                stats[p1]['O'] += 1
                stats[p2]['O'] += 1
                stats[p1]['AG'] += s1
                stats[p1]['YG'] += s2
                stats[p2]['AG'] += s2
                stats[p2]['YG'] += s1
                
                if s1 > s2:
                    stats[p1]['G'] += 1
                    stats[p1]['Puan'] += 3
                    stats[p2]['M'] += 1
                elif s2 > s1:
                    stats[p2]['G'] += 1
                    stats[p2]['Puan'] += 3
                    stats[p1]['M'] += 1
                else:
                    stats[p1]['B'] += 1
                    stats[p1]['Puan'] += 1
                    stats[p2]['B'] += 1
                    stats[p2]['Puan'] += 1

            for p in stats:
                stats[p]['AV'] = stats[p]['AG'] - stats[p]['YG']
            
            df = pd.DataFrame.from_dict(stats, orient='index')
            df = df.sort_values(by=['Puan', 'AV', 'AG'], ascending=False)
            return df

        st.divider()
        st.subheader("📊 Puan Durumları")
        dfA = hesapla_puan(st.session_state.gA, st.session_state.maclarA, st.session_state.skorlarA, "a")
        dfB = hesapla_puan(st.session_state.gB, st.session_state.maclarB, st.session_state.skorlarB, "b")
        
        st.write("#### A Grubu Puan Durumu")
        st.dataframe(dfA, use_container_width=True)
        
        st.write("#### B Grubu Puan Durumu")
        st.dataframe(dfB, use_container_width=True)

# --- TAB 3: YARI FİNAL ---
with tab3:
    st.subheader("🔥 Yarı Final Eşleşmeleri")
    if st.session_state.gA and st.session_state.gB:
        dfA = hesapla_puan(st.session_state.gA, st.session_state.maclarA, st.session_state.skorlarA, "a")
        dfB = hesapla_puan(st.session_state.gB, st.session_state.maclarB, st.session_state.skorlarB, "b")
        
        a1, a2 = dfA.index[0], dfA.index[1]
        b1, b2 = dfB.index[0], dfB.index[1]
        
        st.success(f"**Yarı Final 1:** {a1} (A1)  VS  {b2} (B2)")
        st.warning(f"**Yarı Final 2:** {b1} (B1)  VS  {a2} (A2)")
    else:
        st.info("Kura çekildikten sonra yarı final eşleşmeleri burada görünecektir.")
