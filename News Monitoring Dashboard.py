import pandas as pd
import requests
import streamlit as st
import os
from datetime import datetime

# -----------------------------
# 🔑 API KEY
# -----------------------------
NEWS_API_KEY = "c074f6b4036a4589a36914103ef44c92"

st.set_page_config(layout="wide")

# -----------------------------
# 📄 DATA
# -----------------------------
@st.cache_data
def load_award_data():
    data = [
        {"company": "BP Products North America", "volume": 5000000, "release": "R1"},
        {"company": "Shell Trading (US) Company", "volume": 16200000, "release": "R1"},
        {"company": "Trafigura Trading LLC", "volume": 10030000, "release": "R1.b"},
        {"company": "Marathon Petroleum Company", "volume": 2000000, "release": "R1.b"},
        {"company": "ExxonMobil Oil Corporation", "volume": 3000000, "release": "R1.b"},
        {"company": "Vitol", "volume": 3500000, "release": "R1.b"},
    ]
    return pd.DataFrame(data)

# -----------------------------
# 🧠 SCORING
# -----------------------------
def relevance_score(text):
    keywords = ["oil", "crude", "energy", "petroleum", "refinery", "spr"]
    return sum(1 for k in keywords if k in text.lower())

# -----------------------------
# 📰 NEWS FETCH
# -----------------------------
@st.cache_data(ttl=600)
def fetch_news(companies):
    all_news = []
    for company in companies:
        url = f"https://newsapi.org/v2/everything?q={company}+oil&apiKey={NEWS_API_KEY}"
        try:
            res = requests.get(url)
            articles = res.json().get("articles", [])
        except:
            continue

        for a in articles[:5]:
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
# 📥 SAVE TO EXCEL
# -----------------------------
def save_news(news_df):
    file = "spr_news_log.xlsx"
    news_df["logged_at"] = datetime.now()

    if os.path.exists(file):
        old = pd.read_excel(file)
        news_df = pd.concat([old, news_df])

    news_df = news_df.drop_duplicates(subset=["headline"])
    news_df.to_excel(file, index=False)
    return file

# -----------------------------
# 🎯 UI
# -----------------------------
st.title("🛢️ SPR Intelligence Monitoring Dashboard")

if st.button("🔄 Refresh Data"):

    awards = load_award_data()
    companies = list(awards["company"].unique())
    news_df = fetch_news(companies)

    file_path = save_news(news_df)

    # =============================
    # 📊 KPI ROW
    # =============================
    total = awards["volume"].sum()
    top = awards.groupby("company")["volume"].sum().idxmax()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Barrels", f"{total:,.0f}")
    c2.metric("Companies", awards["company"].nunique())
    c3.metric("Top Player", top)

    # =============================
    # 📢 NEWS TICKER
    # =============================
    if not news_df.empty:
        ticker = " 🔹 ".join(news_df["headline"].head(10))
        st.markdown(f"""
        <marquee style='background:black;color:#00ffcc;padding:10px;font-size:16px;'>
        {ticker}
        </marquee>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # =============================
    # 📺 LIVE MONITORING PANEL
    # =============================
    st.subheader("📺 Live Monitoring")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Reuters Live Feed**")
        st.components.v1.iframe("https://www.reuters.com/world/", height=400)

    with col2:
        st.markdown("**Bloomberg Markets**")
        st.components.v1.iframe("https://www.bloomberg.com/markets", height=400)

    st.markdown("---")

    # =============================
    # 🧠 SIMULATED LIVE NEWS PANEL
    # =============================
    st.subheader("🧠 Live Headlines Feed")

    if not news_df.empty:
        for _, row in news_df.head(5).iterrows():
            st.markdown(f"""
            ### 📰 {row['headline']}
            **{row['company']} | {row['source']} | {row['date']}**
            ---
            """)

    # =============================
    # 📊 ANALYTICS
    # =============================
    st.subheader("📊 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.bar_chart(awards.groupby("company")["volume"].sum())

    with col2:
        st.bar_chart(awards.groupby("release")["volume"].sum())

    st.markdown("---")

    # =============================
    # 📋 DATA TABLE
    # =============================
    st.subheader("📋 SPR Allocation Table")
    st.dataframe(awards)

    # =============================
    # 📥 DOWNLOAD
    # =============================
    st.subheader("📥 Export News")

    with open(file_path, "rb") as f:
        st.download_button("Download Excel", f, "spr_news.xlsx")

else:
    st.info("Click Refresh to load dashboard")
