import pandas as pd
import requests
import streamlit as st
import os
from datetime import datetime
import time

# -----------------------------
# 🔑 SECURE API KEY
# -----------------------------
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]

# -----------------------------
# 📄 DATA
# -----------------------------
@st.cache_data
def load_award_data():
    data = [
        {"company": "Shell Trading (US) Company", "volume": 16200000, "release": "R1"},
        {"company": "Trafigura Trading LLC", "volume": 8860000, "release": "R1"},
        {"company": "Marathon Petroleum Company LP", "volume": 7700000, "release": "R1"},
        {"company": "BP Products North America", "volume": 5000000, "release": "R1"},
        {"company": "Gunvor USA LLC", "volume": 3085000, "release": "R1"},
        {"company": "Mercuria Energy America LLC", "volume": 2000000, "release": "R1"},
        {"company": "Vitol Inc.", "volume": 2000000, "release": "R1"},
        {"company": "Energy Transfer Crude Marketing LLC", "volume": 375000, "release": "R1"},
    ]
    return pd.DataFrame(data)

# -----------------------------
# 🧠 RELEVANCE
# -----------------------------
def relevance_score(text):
    keywords = ["spr", "oil", "crude", "energy", "petroleum", "refinery", "doe"]
    return sum(1 for k in keywords if k in text.lower())

# -----------------------------
# 📰 NEWS
# -----------------------------
@st.cache_data(ttl=600)
def fetch_news(companies):
    all_news = []

    for company in companies:
        query = f'"{company}" AND (oil OR crude OR energy OR petroleum)'

        url = f"https://newsapi.org/v2/everything?q={query}&pageSize=5&apiKey={NEWS_API_KEY}"

        try:
            articles = requests.get(url).json().get("articles", [])
        except:
            continue

        for a in articles:
            score = relevance_score(a["title"])
            if score < 1:
                continue

            all_news.append({
                "company": company,
                "headline": a["title"],
                "date": a["publishedAt"][:10],
                "source": a["source"]["name"],
                "relevance": score
            })

    return pd.DataFrame(all_news)

# -----------------------------
# 📥 SAVE
# -----------------------------
def save_news(news_df):
    path = "spr_news_log.xlsx"
    news_df["logged_at"] = datetime.now()

    if os.path.exists(path):
        old = pd.read_excel(path)
        news_df = pd.concat([old, news_df]).drop_duplicates(subset=["headline"])

    news_df.to_excel(path, index=False)
    return path

# -----------------------------
# 🧠 AI SUMMARY
# -----------------------------
def generate_summary(df):
    top = df.groupby("company")["volume"].sum().idxmax()
    total = df["volume"].sum()

    return f"""
    Total of {total:,} barrels distributed.  
    {top} is the largest recipient.  
    Market is concentrated among few key players.  
    """

# -----------------------------
# 🎯 UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("🛢️ SPR Executive Intelligence Dashboard")

# AUTO REFRESH
refresh_interval = st.sidebar.slider("Auto Refresh (seconds)", 0, 300, 0)

if refresh_interval > 0:
    time.sleep(refresh_interval)
    st.rerun()

if st.button("🔄 Refresh Now"):

    df = load_award_data()
    companies = list(df["company"].unique())
    news_df = fetch_news(companies)

    file_path = save_news(news_df)

    # KPIs
    total = df["volume"].sum()
    top = df.groupby("company")["volume"].sum().idxmax()

    c1, c2 = st.columns(2)
    c1.metric("Total Barrels", f"{total:,}")
    c2.metric("Top Company", top)

    # -----------------------------
    # 🧠 EXEC SUMMARY
    # -----------------------------
    st.subheader("🧠 Executive Summary")
    st.info(generate_summary(df))

    # -----------------------------
    # 📊 MARKET SHARE
    # -----------------------------
    st.subheader("📊 Market Share")
    st.bar_chart(df.groupby("company")["volume"].sum())

    # -----------------------------
    # 📺 LIVE VIDEO
    # -----------------------------
    st.subheader("📺 Live News")

    col1, col2 = st.columns(2)
    with col1:
        st.components.v1.iframe("https://www.youtube.com/embed/9Auq9mYxFEE", height=300)
    with col2:
        st.components.v1.iframe("https://www.youtube.com/embed/dp8PhLsUcFE", height=300)

    # -----------------------------
    # 📢 TICKER
    # -----------------------------
    if not news_df.empty:
        headlines = " 🔹 ".join(news_df["headline"].head(10))
        st.markdown(f"<marquee>{headlines}</marquee>", unsafe_allow_html=True)

    # -----------------------------
    # 🔔 ALERTS
    # -----------------------------
    st.subheader("🚨 Alerts")

    alerts = news_df[news_df["relevance"] >= 3]

    if not alerts.empty:
        for _, r in alerts.iterrows():
            st.warning(f"{r['company']} - {r['headline']}")
    else:
        st.success("No critical alerts")

    # -----------------------------
    # 📥 DOWNLOAD
    # -----------------------------
    with open(file_path, "rb") as f:
        st.download_button("Download News Log", f, "news.xlsx")

else:
    st.info("Click refresh to load dashboard")
