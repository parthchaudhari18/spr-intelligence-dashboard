import pandas as pd
import requests
import streamlit as st
import os
from datetime import datetime

# -----------------------------
# 🔑 API KEY (move to secrets later)
# -----------------------------
NEWS_API_KEY = "c074f6b4036a4589a36914103ef44c92"

# -----------------------------
# 📄 SPR AWARD DATA (SOURCE OF TRUTH)
# -----------------------------
@st.cache_data
def load_award_data():
    data = [
        {"company": "BP Products North America", "volume": 5000000, "release": "R1"},
        {"company": "Energy Transfer Crude Marketing LLC", "volume": 375000, "release": "R1"},
        {"company": "Gunvor USA LLC", "volume": 3085000, "release": "R1"},
        {"company": "Marathon Petroleum Company LP", "volume": 7700000, "release": "R1"},
        {"company": "Mercuria Energy America LLC", "volume": 2000000, "release": "R1"},
        {"company": "Shell Trading (US) Company", "volume": 16200000, "release": "R1"},
        {"company": "Trafigura Trading LLC", "volume": 8860000, "release": "R1"},
        {"company": "Vitol Inc.", "volume": 2000000, "release": "R1"},

        {"company": "Gunvor USA LLC", "volume": 1100000, "release": "R1.a"},
        {"company": "Macquarie Commodities Trading US", "volume": 2000000, "release": "R1.a"},
        {"company": "Phillips 66 Company", "volume": 2900000, "release": "R1.a"},
        {"company": "Trafigura Trading LLC", "volume": 2480000, "release": "R1.a"},

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
    return pd.DataFrame(data)

# -----------------------------
# 🧠 RELEVANCE SCORING
# -----------------------------
def relevance_score(text):
    keywords = ["spr", "oil", "crude", "energy", "petroleum", "refinery", "doe"]
    text = text.lower()
    return sum(1 for k in keywords if k in text)

# -----------------------------
# 📰 FETCH NEWS (NO DUPLICATION)
# -----------------------------
@st.cache_data(ttl=900)
def fetch_all_news(companies):
    all_news = []

    for company in companies:
        query = f'"{company}" AND (oil OR crude OR energy OR petroleum OR refinery OR DOE)'

        url = (
            f"https://newsapi.org/v2/everything?"
            f"q={query}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
        )

        try:
            res = requests.get(url)
            articles = res.json().get("articles", [])
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
# 📥 SAVE NEWS TO EXCEL
# -----------------------------
def save_news_to_excel(news_df):
    file_path = "spr_news_log.xlsx"

    news_df["logged_at"] = datetime.now()

    if os.path.exists(file_path):
        existing_df = pd.read_excel(file_path)
        combined_df = pd.concat([existing_df, news_df], ignore_index=True)
    else:
        combined_df = news_df

    combined_df = combined_df.drop_duplicates(subset=["company", "headline"])
    combined_df.to_excel(file_path, index=False)

    return file_path

# -----------------------------
# 🎯 UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("🛢️ SPR Intelligence Dashboard")

if st.button("🔄 Refresh Data"):

    awards_df = load_award_data()
    companies = list(awards_df["company"].unique())  # FIXED HASH ISSUE
    news_df = fetch_all_news(companies)

    file_path = save_news_to_excel(news_df)

    # -----------------------------
    # 📊 KPIs
    # -----------------------------
    total_barrels = awards_df["volume"].sum()
    total_companies = awards_df["company"].nunique()
    top_company = awards_df.groupby("company")["volume"].sum().idxmax()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Barrels", f"{total_barrels:,.0f}")
    col2.metric("Companies", total_companies)
    col3.metric("Top Recipient", top_company)

    st.markdown("---")

    # -----------------------------
    # 📺 LIVE VIDEO PANEL
    # -----------------------------
    st.subheader("📺 Live News Monitoring")

    col1, col2 = st.columns(2)

    with col1:
       st.markdown("**Reuters Live**")
       st.video("https://www.youtube.com/watch?v=9y9w6WZbq_s")

    with col2:
        st.markdown("**Bloomberg Live**")
        st.video("https://www.youtube.com/watch?v=dp8PhLsUcFE")

    # -----------------------------
    # 📢 NEWS TICKER
    # -----------------------------
    if not news_df.empty:
        headlines = " 🔹 ".join(news_df["headline"].head(15).tolist())

        ticker_html = f"""
        <marquee style='background:black;color:#00ffcc;padding:10px;font-size:18px;'>
        {headlines}
        </marquee>
        """

        st.markdown(ticker_html, unsafe_allow_html=True)

    st.markdown("---")

    # -----------------------------
    # 📊 CHARTS
    # -----------------------------
    st.subheader("📊 Company Ranking")
    st.bar_chart(awards_df.groupby("company")["volume"].sum())

    st.subheader("📈 Barrels by Release")
    st.bar_chart(awards_df.groupby("release")["volume"].sum())

    st.markdown("---")

    # -----------------------------
    # 📋 TABLE
    # -----------------------------
    st.subheader("📋 SPR Awards Table")
    st.dataframe(awards_df, use_container_width=True)

    # -----------------------------
    # 🧠 NEWS ANALYTICS
    # -----------------------------
    if not news_df.empty:
        st.subheader("🧠 News Insights")

        st.write("Top Mentioned Companies")
        st.bar_chart(news_df["company"].value_counts())

        news_df["date"] = pd.to_datetime(news_df["date"], errors="coerce")
        st.write("News Trend")
        st.line_chart(news_df.groupby(news_df["date"].dt.date).size())

        st.markdown("---")

        st.subheader("📰 Top News")
        for _, row in news_df.head(10).iterrows():
            st.markdown(f"""
**{row['company']}**  
📰 {row['headline']}  
📅 {row['date']} | 🏷️ {row['source']}
""")
            st.markdown("---")

    # -----------------------------
    # 📥 DOWNLOAD BUTTON
    # -----------------------------
    st.subheader("📥 Export News Log")

    with open(file_path, "rb") as f:
        st.download_button(
            "Download Excel",
            f,
            "spr_news_log.xlsx"
        )

else:
    st.info("Click refresh to load dashboard")
