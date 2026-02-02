import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import hashlib

# 1. AYARLAR
st.set_page_config(page_title="Midas AI Terminal", layout="wide")

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

USER_DB = "users.csv"
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["username", "password"]).to_csv(USER_DB, index=False)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# 2. GİRİŞ SİSTEMİ
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
                else: st.error("Hatalı!")
            except: st.error("Giriş yapılamadı.")

# 3. ANA PANEL
else:
    p_file = f"portfoy_{st.session_state['user']}.csv"
    if not os.path.exists(p_file):
        pd.DataFrame(columns=["Tarih", "Hisse", "Adet", "Maliyet"]).to_csv(p_file, index=False)

    with st.sidebar:
        st.write(f"👤 {st.session_state['user']}")
        h_kod = st.text_input("Hisse Kodu", "MSFT").upper()
        h_adet = st.number_input("Adet", min_value=0.0, step=0.001)
        h_maliyet = st.number_input("Birim Fiyat ($)", min_value=0.0)
        
        if st.button("Portföye Ekle"):
            if h_adet > 0:
                yeni_veri = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d"), h_kod, h_adet, h_maliyet]], columns=["Tarih", "Hisse", "Adet", "Maliyet"])
                yeni_veri.to_csv(p_file, mode='a', header=False, index=False)
                st.rerun()
        
        if st.button("Güvenli Çıkış"):
            st.session_state["logged_in"] = False
            st.rerun()

    st.title("🛡️ Yatırım Takip Terminali")
    
    try:
        # VERİ ÇEKME
        ticker = yf.Ticker(h_kod)
        # 1 aylık veri çekmeyi dene
        h_chart = ticker.history(period="1mo")
        dolar_hist = yf.Ticker("USDTRY=X").history(period="1d")
        
        if not h_chart.empty:
            current_price = h_chart['Close'].iloc[-1]
            d_kur = dolar_hist['Close'].iloc[-1] if not dolar_hist.empty else 30.0
            
            c1, c2, c3 = st.columns(3)
            c1.metric(f"{h_kod} Fiyat", f"${round(current_price, 2)}")
            c2.metric("USD/TRY Kuru", f"₺{round(d_kur, 2)}")
            
            df_p = pd.read_csv(p_file)
            if not df_p.empty:
                h_ozel = df_p[df_p['Hisse'] == h_kod]
                if not h_ozel.empty:
                    t_adet = h_ozel['Adet'].sum()
                    v_tl = t_adet * current_price * d_kur
                    c3.metric("Senin Varlığın (TL)", f"₺{round(v_tl, 2)}")
            
            # İŞTE O GRAFİK KISMI
            st.subheader(f"📈 {h_kod} 1 Aylık Performans")
            # Sadece Kapanış fiyatlarını içeren temiz bir grafik verisi
            chart_data = h_chart[['Close']]
            st.line_chart(chart_data)
            
            st.divider()
            st.subheader("📜 Tüm İşlemlerin")
            st.dataframe(df_p, use_container_width=True)
        else:
            st.error(f"{h_kod} için veri çekilemedi. Kodun doğruluğundan emin olun.")

    except Exception as e:
        st.error(f"Bir hata oluştu: {e}")
