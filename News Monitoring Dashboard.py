import pandas as pd
import requests
import streamlit as st
import os
from datetime import datetime
import time

# -----------------------------
# 🔑 API KEY
# -----------------------------
NEWS_API_KEY = "c074f6b4036a4589a36914103ef44c92"

# -----------------------------
# 📄 SPR DATA
# -----------------------------
@st.cache_data
def load_award_data():
    data = [
        # Release 1
        {"company": "BP Products North America", "volume": 5000000, "release": "R1"},
        {"company": "Energy Transfer Crude Marketing LLC", "volume": 375000, "release": "R1"},
        {"company": "Gunvor USA LLC", "volume": 3085000, "release": "R1"},
        {"company": "Marathon Petroleum Company LP", "volume": 7700000, "release": "R1"},
        {"company": "Mercuria Energy America LLC", "volume": 2000000, "release": "R1"},
        {"company": "Shell Trading (US) Company", "volume": 16200000, "release": "R1"},
        {"company": "Trafigura Trading LLC", "volume": 8860000, "release": "R1"},
        {"company": "Vitol Inc.", "volume": 2000000, "release": "R1"},

        # Release 1.a
        {"company": "Gunvor USA LLC", "volume": 1100000, "release": "R1.a"},
        {"company": "Macquarie Commodities Trading US", "volume": 2000000, "release": "R1.a"},
        {"company": "Phillips 66 Company", "volume": 2900000, "release": "R1.a"},
        {"company": "Trafigura Trading LLC", "volume": 2480000, "release": "R1.a"},

        # Release 1.b
        {"company": "Alon USA", "volume": 1000000, "release": "R1.b"},
        {"company": "BP Products North America", "volume": 1000000, "release": "R1.b"},
        {"company": "Energy Transfer Crude Marketing", "volume": 1100000, "release": "R1.b"},
        {"company": "ExxonMobil Oil Corporation", "volume": 3000000, "release": "R1.b"},
        {"company": "Macquarie Commodities Trading US", "volume": 2500000, "release": "R1.b"},
        {"company": "Marathon Petroleum Company", "volume": 2000000, "release": "R1.b"},
        {"company": "Shell Trading (US) Company", "volume": 1900000, "release": "R1.b"},
        {"company": "Trafigura Trading LLC", "volume": 10030000, "release": "R1.b"},
        {"company": "Vitol", "volume": 3500000, "release": "R1.b"},
    ]

    df = pd.DataFrame(data)
    return df

# -----------------------------
# 🧠 RELEVANCE
# -----------------------------
def relevance_score(text):
    keywords = ["oil", "crude", "energy", "petroleum", "refinery", "spr"]
    return sum(1 for k in keywords if k in text.lower())

# -----------------------------
# 📰 FETCH NEWS
# -----------------------------
@st.cache_data(ttl=600)
def fetch_all_news(companies):
    news = []

    for company in companies:
        url = f"https://newsapi.org/v2/everything?q={company} oil&apiKey={NEWS_API_KEY}&pageSize=5"

        try:
            res = requests.get(url)
            articles = res.json().get("articles", [])
        except:
            continue

        for a in articles:
            score = relevance_score(a["title"])
            if score < 1:
                continue

            news.append({
                "company": company,
                "headline": a["title"],
                "date": a["publishedAt"][:10],
                "source": a["source"]["name"],
                "relevance": score
            })

    return pd.DataFrame(news)

# -----------------------------
# 📥 SAVE NEWS
# -----------------------------
def save_news_to_excel(news_df):
    file_path = "spr_news_log.xlsx"
    news_df["logged_at"] = datetime.now()

    if os.path.exists(file_path):
        existing = pd.read_excel(file_path)
        news_df = pd.concat([existing, news_df]).drop_duplicates(subset=["headline"])

    news_df.to_excel(file_path, index=False)
    return file_path

# -----------------------------
# 🎯 UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("🛢️ SPR Intelligence Dashboard")

if st.button("🔄 Refresh Dashboard"):

    awards = load_award_data()
    news_df = fetch_all_news(list(awards["company"].unique()))
    file_path = save_news_to_excel(news_df)

    # KPIs
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Barrels", f"{awards['volume'].sum():,}")
    c2.metric("Companies", awards["company"].nunique())
    c3.metric("Top Company", awards.groupby("company")["volume"].sum().idxmax())

    st.markdown("---")

    # -----------------------------
    # 📢 STOCK-STYLE NEWS TICKER
    # -----------------------------
    if not news_df.empty:

        headlines = "  ♦  ".join(news_df["headline"].head(15).tolist())

        ticker_html = f"""
        <style>
        .ticker-container {{
            width: 100%;
            overflow: hidden;
            background: linear-gradient(90deg, #000000, #1a1a1a);
            border-top: 2px solid #00ffcc;
            border-bottom: 2px solid #00ffcc;
            padding: 10px 0;
            position: relative;
        }}

        .ticker-text {{
            display: inline-block;
            white-space: nowrap;
            animation: scroll-left 25s linear infinite;
            font-size: 18px;
            font-weight: 600;
            color: #00ffcc;
        }}

        @keyframes scroll-left {{
            0% {{
                transform: translateX(100%);
            }}
            100% {{
                transform: translateX(-100%);
            }}
        }}
        </style>

        <div class="ticker-container">
            <div class="ticker-text">
                {headlines}
            </div>
        </div>
        """

        st.markdown(ticker_html, unsafe_allow_html=True)
    # -----------------------------
# 📢 PROFESSIONAL STOCK TICKER (SLOW + SMOOTH)
# -----------------------------
if not news_df.empty:

    headlines = "   ◆   ".join(
        [f"{row['company']}: {row['headline']}" for _, row in news_df.head(12).iterrows()]
    )

    ticker_html = f"""
    <style>
    .ticker-container {{
        width: 100%;
        overflow: hidden;
        background: #0a0a0a;
        border-top: 1px solid #00ffcc;
        border-bottom: 1px solid #00ffcc;
        padding: 12px 0;
    }}

    .ticker-track {{
        display: flex;
        width: max-content;
        animation: scroll-left 60s linear infinite;
    }}

    .ticker-item {{
        margin-right: 80px;
        font-size: 17px;
        font-weight: 500;
        color: #00ffcc;
    }}

    @keyframes scroll-left {{
        from {{
            transform: translateX(0%);
        }}
        to {{
            transform: translateX(-50%);
        }}
    }}
    </style>

    <div class="ticker-container">
        <div class="ticker-track">
            {"".join([f"<div class='ticker-item'>{h}</div>" for h in headlines.split("   ◆   ")])}
            {"".join([f"<div class='ticker-item'>{h}</div>" for h in headlines.split("   ◆   ")])}
        </div>
    </div>
    """

    st.markdown(ticker_html, unsafe_allow_html=True)
    # 📊 CHARTS
    st.subheader("📊 Company Allocation")
    st.bar_chart(awards.groupby("company")["volume"].sum())

    st.subheader("📈 News Relevance Distribution")
    if not news_df.empty:
        st.bar_chart(news_df["relevance"].value_counts())

    st.markdown("---")

    # 📋 TABLE
    st.subheader("📋 SPR Data")
    st.dataframe(awards)

    # 📥 DOWNLOAD
    with open(file_path, "rb") as f:
        st.download_button("Download News Log", f, "news.xlsx")

else:
    st.info("Click refresh to load dashboard")
