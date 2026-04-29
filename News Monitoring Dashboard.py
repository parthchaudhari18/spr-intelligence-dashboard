import pandas as pd
import requests
import streamlit as st

# -----------------------------
# 🔑 API KEY (regen later)
# -----------------------------
NEWS_API_KEY = "c074f6b4036a4589a36914103ef44c92"

# -----------------------------
# 📄 SPR AWARD DATA
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
def relevance_score(text: str) -> int:
    keywords = {
        "strategic petroleum reserve": 3,
        "spr": 3,
        "oil": 2,
        "crude": 2,
        "energy": 1,
        "refinery": 2,
        "petroleum": 2,
        "pipeline": 1,
        "export": 1,
        "doe": 2
    }
    t = text.lower()
    return sum(v for k, v in keywords.items() if k in t)

# -----------------------------
# 📰 FETCH NEWS (BROADER + SCORING)
# -----------------------------
@st.cache_data(ttl=900)  # cache 15 mins
def fetch_news_for_company(company: str):
    query = f'"{company}" AND ("oil" OR "crude" OR "energy" OR refinery OR DOE OR petroleum)'

    url = (
        "https://newsapi.org/v2/everything?"
        f"q={query}"
        "&language=en"
        "&sortBy=publishedAt"
        "&pageSize=10"
        f"&apiKey={NEWS_API_KEY}"
    )

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("status") != "ok":
            return []
        articles = data.get("articles", [])
    except Exception:
        return []

    out = []
    for a in articles:
        title = a.get("title", "") or ""
        score = relevance_score(title)
        if score < 1:
            continue  # keep mildly relevant+
        out.append({
            "company": company,
            "headline": title,
            "date": (a.get("publishedAt") or "")[:10],
            "source": (a.get("source") or {}).get("name", ""),
            "relevance": score
        })
    return out

# -----------------------------
# 🧠 SENTIMENT (simple)
# -----------------------------
def simple_sentiment(text: str) -> str:
    pos = ["growth", "profit", "expand", "increase", "gain", "rise"]
    neg = ["loss", "decline", "drop", "risk", "fall", "cut"]
    t = text.lower()
    score = sum(1 for w in pos if w in t) - sum(1 for w in neg if w in t)
    return "Positive" if score > 0 else "Negative" if score < 0 else "Neutral"

# -----------------------------
# 🔄 BUILD DATASET
# -----------------------------
@st.cache_data(ttl=900)
def build_dataset():
    awards = load_award_data()

    all_news = []
    for c in awards["company"].unique():
        for item in fetch_news_for_company(c):
            item["sentiment"] = simple_sentiment(item["headline"])
            all_news.append(item)

    news_df = pd.DataFrame(all_news)

    # sort by relevance desc
    if not news_df.empty:
        news_df = news_df.sort_values(by="relevance", ascending=False)

    final_df = awards.merge(news_df, on="company", how="left")
    return final_df, news_df

# -----------------------------
# 🎯 UI
# -----------------------------
st.set_page_config(page_title="SPR Intelligence Dashboard", layout="wide")
st.title("🛢️ SPR Intelligence Dashboard")
st.markdown("**SPR allocations + broader oil/energy news with relevance scoring**")

if st.button("🔄 Refresh Data"):
    data, news_df = build_dataset()

    # KPIs
    total_barrels = data["volume"].sum()
    total_companies = data["company"].nunique()
    top_company = data.groupby("company")["volume"].sum().idxmax()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Barrels", f"{total_barrels:,.0f}")
    c2.metric("Companies", total_companies)
    c3.metric("Top Recipient", top_company)

    st.markdown("---")

    # Filters
    colf1, colf2 = st.columns(2)
    with colf1:
        selected_companies = st.multiselect(
            "Companies",
            options=sorted(data["company"].unique()),
            default=sorted(data["company"].unique())
        )
    with colf2:
        selected_release = st.multiselect(
            "Releases",
            options=sorted(data["release"].unique()),
            default=sorted(data["release"].unique())
        )

    filtered = data[
        data["company"].isin(selected_companies) &
        data["release"].isin(selected_release)
    ]

    # Charts
    st.subheader("📊 Company Ranking (Barrels)")
    ranking = filtered.groupby("company")["volume"].sum().sort_values(ascending=False)
    st.bar_chart(ranking)

    st.subheader("📈 Barrels by Release")
    st.bar_chart(filtered.groupby("release")["volume"].sum())

    # News analytics
    st.subheader("🧠 News Analytics")

    if not news_df.empty:
        # Top mentioned companies (news count)
        mentions = news_df["company"].value_counts().head(10)
        st.write("**Top Mentioned Companies (News Count)**")
        st.bar_chart(mentions)

        # Trend over time
        news_df["date"] = pd.to_datetime(news_df["date"], errors="coerce")
        trend = news_df.dropna(subset=["date"]).groupby(news_df["date"].dt.date).size()
        st.write("**News Trend Over Time**")
        st.line_chart(trend)

    st.markdown("---")

    # Detailed table
    st.subheader("📋 Detailed Table")

    def highlight(row):
        if row.get("sentiment") == "Negative" and row["volume"] > filtered["volume"].median():
            return ["background-color: #ffcccc"] * len(row)
        return [""] * len(row)

    st.dataframe(filtered.style.apply(highlight, axis=1), use_container_width=True)

    # News panel (sorted by relevance)
    st.subheader("📰 Top Relevant News")
    if not news_df.empty:
        for _, r in news_df.head(12).iterrows():
            st.markdown(f"""
**{r['company']}**  
📰 {r['headline']}  
📅 {r['date']} | 🏷️ {r['source']} | 🔎 Relevance: {r['relevance']}
""")
            st.markdown("---")
    else:
        st.info("No news found for current filters.")

else:
    st.info("Click 'Refresh Data' to load dashboard.")