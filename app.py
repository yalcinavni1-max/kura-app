import streamlit as st
import random
import math
import pandas as pd
import json
import os

st.set_page_config(page_title="Turnuva Yönetim Sistemi", layout="centered", page_icon="🏆")

KAYIT_DOSYASI = "turnuva_durumu.json"

# --- VERİ KAYDETME VE YÜKLEME FONKSİYONLARI ---
def verileri_kaydet():
    durum = {
        'oyuncular': st.session_state.get('oyuncular', []),
        'gA': st.session_state.get('gA', []),
        'gB': st.session_state.get('gB', []),
        'maclarA': st.session_state.get('maclarA', []),
        'maclarB': st.session_state.get('maclarB', []),
        'skorlarA': st.session_state.get('skorlarA', {}),
        'skorlarB': st.session_state.get('skorlarB', {})
    }
    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=4)

def verileri_yukle():
    if os.path.exists(KAYIT_DOSYASI):
        try:
            with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f:
                durum = json.load(f)
                st.session_state.oyuncular = durum.get('oyuncular', [])
                st.session_state.gA = durum.get('gA', [])
                st.session_state.gB = durum.get('gB', [])
                st.session_state.maclarA = [tuple(x) for x in durum.get('maclarA', [])]
                st.session_state.maclarB = [tuple(x) for x in durum.get('maclarB', [])]
                st.session_state.skorlarA = durum.get('skorlarA', {})
                st.session_state.skorlarB = durum.get('skorlarB', {})
        except Exception:
            pass

# Uygulama açıldığında kayıtlı veri varsa otomatik yükle
if 'yuklendi' not in st.session_state:
    verileri_yukle()
    st.session_state.yuklendi = True

st.title("🏆 Turnuva Yönetim Sistemi")

tab1, tab2, tab3 = st.tabs(["🎲 Kura & Oyuncular", "⚽ Grup Maçları & Puan", "🏆 Yarı Final"])

# --- AKILLI ÇAKIŞMASIZ MAÇ DİZİCİ ---
def akilli_cakismasiz_maclar(grup):
    tum_maclar = []
    for i in range(len(grup)):
        for j in range(i + 1, len(grup)):
            tum_maclar.append((grup[i], grup[j]))
    
    toplam_mac = len(tum_maclar)
    sirali_maclar = []
    kullanildi = [False] * toplam_mac
    
    for _ in range(toplam_mac):
        eklendi = False
        indeksler = list(range(toplam_mac))
        random.shuffle(indeksler)
        
        for k in indeksler:
            if not kullanildi[k]:
                p1, p2 = tum_maclar[k]
                uygun = True
                
                if len(sirali_maclar) > 0:
                    prev_p1, prev_p2 = sirali_maclar[-1]
                    if p1 == prev_p1 or p1 == prev_p2 or p2 == prev_p1 or p2 == prev_p2:
                        uygun = False
                
                if uygun:
                    sirali_maclar.append((p1, p2))
                    kullanildi[k] = True
                    eklendi = True
                    break
        
        if not eklendi:
            for k in range(toplam_mac):
                if not kullanildi[k]:
                    sirali_maclar.append(tum_maclar[k])
                    kullanildi[k] = True
                    break
                    
    return sirali_maclar

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
            
            yari = math.ceil(len(oyuncular) / 2)
            st.session_state.gA = oyuncular[:yari]
            st.session_state.gB = oyuncular[yari:]
            
            st.session_state.maclarA = akilli_cakismasiz_maclar(st.session_state.gA)
            st.session_state.maclarB = akilli_cakismasiz_maclar(st.session_state.gB)
            st.session_state.skorlarA = {}
            st.session_state.skorlarB = {}
            
            # Kura çekilince anında kaydet
            verileri_kaydet()
            st.success("Kura çekildi ve güvenli hafızaya kaydedildi!")

    if col2.button("🗑️ Turnuvayı Sıfırla", use_container_width=True):
        st.session_state.clear()
        if os.path.exists(KAYIT_DOSYASI):
            os.remove(KAYIT_DOSYASI)
        st.rerun()

    if st.session_state.get('gA'):
        c1, c2 = st.columns(2)
        with c1:
            st.write("### A Grubu")
            for p in st.session_state.gA:
                st.info(p)
        with c2:
            st.write("### B Grubu")
            for p in st.session_state.gB:
                st.warning(p)

# Puan Durumu Hesaplama
def hesapla_puan(grup, maclar, skorlar):
    stats = {p: {'O': 0, 'G': 0, 'B': 0, 'M': 0, 'AG': 0, 'YG': 0, 'AV': 0, 'Puan': 0} for p in grup}
    for idx, (p1, p2) in enumerate(maclar):
        s1 = skorlar.get(f"{idx}_1", 0)
        s2 = skorlar.get(f"{idx}_2", 0)
        
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

# --- TAB 2: MAÇLAR VE PUAN DURUMU ---
with tab2:
    if not st.session_state.get('maclarA'):
        st.info("Lütfen önce Kura Çekin.")
    else:
        degisiklik_var_mi = False
        
        st.subheader("⚽ A Grubu Maçları")
        for idx, (p1, p2) in enumerate(st.session_state.maclarA):
            col_m, col_s1, col_s2 = st.columns([2, 1, 1])
            col_m.write(f"**{idx+1}. Maç:** {p1} vs {p2}")
            
            eski_s1 = st.session_state.skorlarA.get(f"{idx}_1", 0)
            eski_s2 = st.session_state.skorlarA.get(f"{idx}_2", 0)
            
            s1 = col_s1.number_input(f"{p1}", min_value=0, max_value=20, key=f"a_{idx}_1", value=eski_s1)
            s2 = col_s2.number_input(f"{p2}", min_value=0, max_value=20, key=f"a_{idx}_2", value=eski_s2)
            
            if s1 != eski_s1 or s2 != eski_s2:
                st.session_state.skorlarA[f"{idx}_1"] = s1
                st.session_state.skorlarA[f"{idx}_2"] = s2
                degisiklik_var_mi = True

        st.divider()
        st.subheader("⚽ B Grubu Maçları")
        for idx, (p1, p2) in enumerate(st.session_state.maclarB):
            col_m, col_s1, col_s2 = st.columns([2, 1, 1])
            col_m.write(f"**{idx+1}. Maç:** {p1} vs {p2}")
            
            eski_s1 = st.session_state.skorlarB.get(f"{idx}_1", 0)
            eski_s2 = st.session_state.skorlarB.get(f"{idx}_2", 0)
            
            s1 = col_s1.number_input(f"{p1}", min_value=0, max_value=20, key=f"b_{idx}_1", value=eski_s1)
            s2 = col_s2.number_input(f"{p2}", min_value=0, max_value=20, key=f"b_{idx}_2", value=eski_s2)
            
            if s1 != eski_s1 or s2 != eski_s2:
                st.session_state.skorlarB[f"{idx}_1"] = s1
                st.session_state.skorlarB[f"{idx}_2"] = s2
                degisiklik_var_mi = True

        # Skor değiştiyse anında dosyaya kaydet
        if degisiklik_var_mi:
            verileri_kaydet()

        st.divider()
        st.subheader("📊 Puan Durumları")
        dfA = hesapla_puan(st.session_state.gA, st.session_state.maclarA, st.session_state.skorlarA)
        dfB = hesapla_puan(st.session_state.gB, st.session_state.maclarB, st.session_state.skorlarB)
        
        st.write("#### A Grubu Puan Durumu")
        st.dataframe(dfA, use_container_width=True)
        
        st.write("#### B Grubu Puan Durumu")
        st.dataframe(dfB, use_container_width=True)

# --- TAB 3: YARI FİNAL ---
with tab3:
    st.subheader("🔥 Yarı Final Eşleşmeleri")
    if st.session_state.get('gA') and st.session_state.get('gB'):
        dfA = hesapla_puan(st.session_state.gA, st.session_state.maclarA, st.session_state.skorlarA)
        dfB = hesapla_puan(st.session_state.gB, st.session_state.maclarB, st.session_state.skorlarB)
        
        a1, a2 = dfA.index[0], dfA.index[1]
        b1, b2 = dfB.index[0], dfB.index[1]
        
        st.success(f"**Yarı Final 1:** {a1} (A1)  VS  {b2} (B2)")
        st.warning(f"**Yarı Final 2:** {b1} (B1)  VS  {a2} (A2)")
    else:
        st.info("Kura çekildikten sonra yarı final eşleşmeleri burada görünecektir.")
