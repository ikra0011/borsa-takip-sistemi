import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import hashlib

# 1. TEMEL AYARLAR (HATA KORUMALI)
st.set_page_config(page_title="Midas AI Terminal", layout="wide")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

USER_DB = "users.csv"
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["username", "password"]).to_csv(USER_DB, index=False)

# 2. OTURUM YÖNETİMİ
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Midas Cloud Giriş")
    tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
    with tab2:
        u = st.text_input("Kullanıcı Adı Seç", key="reg_u")
        p = st.text_input("Şifre Seç", type='password', key="reg_p")
        if st.button("Kayıt Ol"):
            if u and p:
                df_u = pd.read_csv(USER_DB)
                if u not in df_u['username'].values.astype(str):
                    pd.DataFrame([[u, make_hashes(p)]], columns=["username", "password"]).to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Hesap oluşturuldu, Giriş sekmesine tıkla!")
                else: st.error("Bu kullanıcı adı alınmış.")
    with tab1:
        u_log = st.text_input("Kullanıcı Adı", key="log_u")
        p_log = st.text_input("Şifre", type='password', key="log_p")
        if st.button("Giriş Yap"):
            try:
                df_u = pd.read_csv(USER_DB)
                user_row = df_u[df_u['username'].astype(str) == u_log]
                if not user_row.empty and check_hashes(p_log, user_row['password'].values[0]):
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = u_log
                    st.rerun()
                else: st.error("Hatalı giriş!")
            except: st.error("Giriş yapılamadı.")

# 3. ANA PANEL (GİRİŞ YAPILDIYSA)
else:
    p_file = f"portfoy_{st.session_state['user']}.csv"
    if not os.path.exists(p_file):
        pd.DataFrame(columns=["Tarih", "Hisse", "Adet", "Maliyet"]).to_csv(p_file, index=False)

    with st.sidebar:
        st.write(f"👤 Kullanıcı: {st.session_state['user']}")
        h_kod = st.text_input("Hisse (Örn: MSFT)", "MSFT").upper()
        h_adet = st.number_input("Adet", min_value=0.0, step=0.001)
        h_maliyet = st.number_input("Birim Fiyat ($)", min_value=0.0)
        
        if st.button("Portföye Ekle"):
            if h_adet > 0:
                yeni_veri = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), h_kod, h_adet, h_maliyet]], columns=["Tarih", "Hisse", "Adet", "Maliyet"])
                yeni_veri.to_csv(p_file, mode='a', header=False, index=False)
                st.balloons()
                st.rerun()
        
        if st.button("Güvenli Çıkış"):
            st.session_state["logged_in"] = False
            st.rerun()

    st.title("🛡️ Yatırım Takip Terminali")
    
    # VERİ ÇEKME (EN GÜVENLİ HALE GETİRİLDİ)
    try:
        # Yahoo Finance verilerini çek
        h_fiyat, d_kur = 0.0, 30.0 # Varsayılan değerler
        
        ticker = yf.Ticker(h_kod)
        h_hist = ticker.history(period="1d")
        if not h_hist.empty:
            h_fiyat = h_hist['Close'].iloc[-1]
            
        dolar_hist = yf.Ticker("USDTRY=X").history(period="1d")
        if not dolar_hist.empty:
            d_kur = dolar_hist['Close'].iloc[-1]
        
        # Göstergeler
        c1, c2, c3 = st.columns(3)
        c1.metric(f"{h_kod} Fiyat", f"${round(h_fiyat, 2)}")
        c2.metric("USD/TRY Kuru", f"₺{round(d_kur, 2)}")
        
        # Portföy Hesaplama
        df_p = pd.read_csv(p_file)
        if not df_p.empty:
            hisse_ozel = df_p[df_p['Hisse'] == h_kod]
            if not hisse_ozel.empty:
                toplam_adet = hisse_ozel['Adet'].sum()
                deger_tl = toplam_adet * h_fiyat * d_kur
                c3.metric("Senin Varlığın (TL)", f"₺{round(deger_tl, 2)}")
            
            st.divider()
            st.subheader("📜 İşlem Geçmişi")
            st.dataframe(df_p, use_container_width=True)
            
            # Grafik (Hata korumalı)
            st.subheader(f"📈 {h_kod} Seyir")
            h_chart = ticker.history(period="1mo")
            if not h_chart.empty:
                st.line_chart(h_chart['Close'])
        else:
            st.info("Portföyün henüz boş. Sol menüden ilk işlemini ekle!")

    except Exception as e:
        st.error(f"Veri çekilemiyor. Hisse kodunu kontrol edin.")


