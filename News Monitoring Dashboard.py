import pandas as pd
import requests
import streamlit as st

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
    return pd.DataFrame(data)

# -----------------------------
# 🧠 RELEVANCE SCORING
# -----------------------------
def relevance_score(text):
    keywords = ["spr", "oil", "crude", "energy", "petroleum", "refinery", "doe"]
    text = text.lower()
    return sum(1 for k in keywords if k in text)

# -----------------------------
# 📰 FETCH NEWS (NO MERGE)
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
# 🎯 UI
# -----------------------------
st.set_page_config(layout="wide")
st.title("🛢️ SPR Intelligence Dashboard")

if st.button("🔄 Refresh Data"):

    awards_df = load_award_data()   # ✅ SOURCE OF TRUTH
    news_df = fetch_all_news(awards_df["company"].unique())

    # -----------------------------
    # ✅ KPIs (CORRECT)
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
    # 📊 CHARTS (CORRECT)
    # -----------------------------
    st.subheader("📊 Company Ranking")
    ranking = awards_df.groupby("company")["volume"].sum().sort_values(ascending=False)
    st.bar_chart(ranking)

    st.subheader("📈 Barrels by Release")
    release_dist = awards_df.groupby("release")["volume"].sum()
    st.bar_chart(release_dist)

    st.markdown("---")

    # -----------------------------
    # 📋 TABLE (NO DUPLICATION)
    # -----------------------------
    st.subheader("📋 SPR Awards Table")
    st.dataframe(awards_df, use_container_width=True)

    # -----------------------------
    # 📰 NEWS ANALYTICS
    # -----------------------------
    st.subheader("🧠 News Insights")

    if not news_df.empty:
        # Top mentioned companies
        mentions = news_df["company"].value_counts()
        st.write("Top Mentioned Companies")
        st.bar_chart(mentions)

        # Trend
        news_df["date"] = pd.to_datetime(news_df["date"], errors="coerce")
        trend = news_df.groupby(news_df["date"].dt.date).size()
        st.write("News Trend")
        st.line_chart(trend)

        st.markdown("---")

        # News feed
        st.subheader("📰 Relevant News")
        for _, row in news_df.sort_values("relevance", ascending=False).head(10).iterrows():
            st.markdown(f"""
**{row['company']}**  
📰 {row['headline']}  
📅 {row['date']} | 🏷️ {row['source']} | 🔎 {row['relevance']}
""")
            st.markdown("---")
    else:
        st.info("No news found")

else:
    st.info("Click refresh to load dashboard")
