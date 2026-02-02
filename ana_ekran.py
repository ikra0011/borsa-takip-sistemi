import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import hashlib

# 1. TEMEL AYARLAR
st.set_page_config(page_title="Midas AI Pro", layout="wide")

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
    st.title("🔐 Giriş Paneli")
    tab1, tab2 = st.tabs(["Giriş", "Kayıt"])
    with tab2:
        u = st.text_input("Kullanıcı Adı", key="u1")
        p = st.text_input("Şifre", type='password', key="p1")
        if st.button("Kayıt Ol"):
            df = pd.read_csv(USER_DB)
            if u not in df['username'].values.astype(str):
                pd.DataFrame([[u, make_hashes(p)]], columns=["username", "password"]).to_csv(USER_DB, mode='a', header=False, index=False)
                st.success("Kayıt oldu, girişe geç!")
    with tab1:
        u_log = st.text_input("Kullanıcı Adı", key="u2")
        p_log = st.text_input("Şifre", type='password', key="p2")
        if st.button("Giriş Yap"):
            try:
                df = pd.read_csv(USER_DB)
                user_row = df[df['username'].astype(str) == u_log]
                if not user_row.empty and check_hashes(p_log, user_row['password'].values[0]):
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = u_log
                    st.rerun()
                else: st.error("Hatalı!")
            except: st.error("Dosya okunurken hata oluştu.")

# 3. ANA EKRAN
else:
    st.title(f"🚀 Hoş geldin {st.session_state['user']}")
    p_file = f"portfoy_{st.session_state['user']}.csv"
    if not os.path.exists(p_file):
        pd.DataFrame(columns=["Tarih", "Hisse", "Adet", "Maliyet"]).to_csv(p_file, index=False)

    with st.sidebar:
        h_kod = st.text_input("Hisse", "MSFT").upper()
        h_adet = st.number_input("Adet", min_value=0.0, step=0.001)
        h_maliyet = st.number_input("Maliyet ($)", min_value=0.0)
        if st.button("Ekle"):
            pd.DataFrame([[datetime.now(), h_kod, h_adet, h_maliyet]], columns=["Tarih", "Hisse", "Adet", "Maliyet"]).to_csv(p_file, mode='a', header=False, index=False)
            st.rerun()
        if st.button("Çıkış"):
            st.session_state["logged_in"] = False
            st.rerun()

    # VERİ ÇEKME (EN RİSKLİ YER)
    try:
        h_fiyat = yf.Ticker(h_kod).history(period="1d")['Close'].iloc[-1]
        kur = yf.Ticker("USDTRY=X").history(period="1d")['Close'].iloc[-1]
        
        c1, c2 = st.columns(2)
        c1.metric("Hisse Fiyat", f"${round(h_fiyat, 2)}")
        c2.metric("Dolar Kuru", f"₺{round(kur, 2)}")
        
        df_p = pd.read_csv(p_file)
        if not df_p.empty:
            st.write("---")
            st.subheader("İşlem Geçmişi")
            st.table(df_p)
    except Exception as e:
        st.warning("Veriler çekilemiyor, piyasa kapalı veya internet zayıf olabilir.")
