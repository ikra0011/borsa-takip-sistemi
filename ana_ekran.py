import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime
import hashlib

# 1. SAYFA VE GÜVENLİK AYARLARI
st.set_page_config(page_title="Midas AI Pro Terminal", layout="wide", page_icon="🤖")

# Şık Görünüm İçin CSS
st.markdown("""
    <style>
    .stMetric { background-color: #1e293b; padding: 20px; border-radius: 15px; border: 1px solid #3b82f6; }
    .ai-box { background-color: #0f172a; padding: 20px; border-radius: 15px; border-left: 5px solid #10b981; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    return make_hashes(password) == hashed_text

# Kullanıcı veritabanını oluştur (Bulut simülasyonu)
USER_DB = "users.csv"
if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["username", "password"]).to_csv(USER_DB, index=False)

# --- 2. GİRİŞ VE KAYIT KONTROLÜ ---
# Session State başlatma
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user" not in st.session_state:
    st.session_state["user"] = ""

if not st.session_state["logged_in"]:
    st.title("🔐 Midas Cloud: Güvenli Giriş")
    tab1, tab2 = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab2:
        new_user = st.text_input("Kullanıcı Adı Seç", key="reg_u")
        new_pass = st.text_input("Şifre Seç", type='password', key="reg_p")
        if st.button("Kayıt Ol", key="reg_btn"):
            if new_user and new_pass:
                df_u = pd.read_csv(USER_DB)
                if new_user not in df_u['username'].values.astype(str):
                    pd.DataFrame([[new_user, make_hashes(new_pass)]], columns=["username", "password"]).to_csv(USER_DB, mode='a', header=False, index=False)
                    st.success("Kayıt başarılı! Giriş sekmesine geçebilirsin.")
                else: st.error("Bu kullanıcı adı alınmış.")
            else: st.warning("Lütfen tüm alanları doldur.")

    with tab1:
        user = st.text_input("Kullanıcı Adı", key="log_u")
        pw = st.text_input("Şifre", type='password', key="log_p")
        if st.button("Giriş", key="log_btn"):
            try:
                df_u = pd.read_csv(USER_DB)
                user_row = df_u[df_u['username'].astype(str) == user]
                if not user_row.empty and check_hashes(pw, user_row['password'].values[0]):
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Hatalı kullanıcı adı veya şifre!")
            except Exception as e:
                st.error(f"Giriş sırasında bir hata oluştu. Lütfen users.csv dosyasını silip tekrar deneyin.")

# --- 3. ANA UYGULAMA (GİRİŞ YAPILDIKTAN SONRA) ---
else:
    USER_PORTFOLIO = f"portfoy_{st.session_state['user']}.csv"
    if not os.path.exists(USER_PORTFOLIO):
        pd.DataFrame(columns=["Tarih", "Hisse", "Adet", "Maliyet"]).to_csv(USER_PORTFOLIO, index=False)

    # SOL MENÜ
    with st.sidebar:
        st.title(f"🤖 {st.session_state['user']} AI Üssü")
        hisse_kod = st.text_input("Hisse", "MSFT").upper()
        adet = st.number_input("Adet", min_value=0.0, value=0.0, format="%.4f")
        maliyet = st.number_input("Alış Fiyatı ($)", min_value=0.0, value=0.0)
        
        if st.button("Portföye İşle 🚀"):
            if adet > 0:
                yeni = pd.DataFrame([[datetime.now().strftime("%Y-%m-%d %H:%M"), hisse_kod, adet, maliyet]], columns=["Tarih", "Hisse", "Adet", "Maliyet"])
                yeni.to_csv(USER_PORTFOLIO, mode='a', header=False, index=False)
                st.balloons()
                st.rerun()
        
        st.divider()
        if st.button("Çıkış Yap"):
            st.session_state["logged_in"] = False
            st.session_state["user"] = ""
            st.rerun()

    # VERİ ÇEKME (Yahoo Finance API)
    @st.cache_data(ttl=60)
    def verileri_al(hisse):
        try:
            h = yf.Ticker(hisse).history(period="1d")['Close'].iloc[-1]
            d = yf.Ticker("USDTRY=X").history(period="1d")['Close'].iloc[-1]
            return h, d
        except:
            return 0.0, 30.0

    fiyat, kur = verileri_al(hisse_kod)
    df_p = pd.read_csv(USER_PORTFOLIO)

    st.title("🛡️ Midas AI Yatırım Terminali")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("USD/TRY Kuru", f"₺{round(kur, 2)}")
    c2.metric(f"{hisse_kod} Fiyat", f"${round(fiyat, 2)}")

    if not df_p.empty:
        hisse_df = df_p[df_p['Hisse'] == hisse_kod]
        if not hisse_df.empty:
            t_adet = hisse_df['Adet'].sum()
            t_maliyet_usd = (hisse_df['Adet'] * hisse_df['Maliyet']).sum()
            su_anki_usd = t_adet * fiyat
            su_anki_tl = su_anki_usd * kur
            kar_zarar_usd = su_anki_usd - t_maliyet_usd
            kar_zarar_tl = kar_zarar_usd * kur

            c3.metric("Varlık (TL)", f"₺{round(su_anki_tl, 2)}")
            c4.metric("Kâr/Zarar (TL)", f"₺{round(kar_zarar_tl, 2)}", f"{round(kar_zarar_usd, 2)}$")

            st.divider()
            st.subheader("🔮 AI Yatırım Yorumcusu")
            msg = "🟢 Kardasın!" if kar_zarar_usd > 0 else "🔴 Zarardasın ama Microsoft sağlamdır."
            st.markdown(f"""<div class="ai-box">{msg} | Dolar: ₺{round(kur,2)}</div>""", unsafe_allow_html=True)

            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader(f"📈 {hisse_kod}")
                st.line_chart(yf.Ticker(hisse_kod).history(period="1mo")['Close'])
            with col_r:
                st.subheader("💵 USD/TRY")
                st.line_chart(yf.Ticker("USDTRY=X").history(period="1mo")['Close'])
            
            st.divider()
            st.subheader("📜 İşlem Geçmişi")
            st.dataframe(df_p, use_container_width=True)
    else:
        st.info("👋 Portföyün boş. Sol menüden ilk alımını ekle!")