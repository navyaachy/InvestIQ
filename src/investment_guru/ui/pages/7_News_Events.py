from __future__ import annotations

from datetime import datetime
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests
import streamlit as st


st.set_page_config(
    page_title="InvestIQ | News & Events",
    page_icon="📰",
    layout="wide",
)

st.title("News & Event Context")
st.caption(
    "Recent company news and market context for portfolio holdings. "
    "News is presented as information, not as a trading recommendation."
)

holdings = st.session_state.get("portfolio_holdings", [])

tickers = []

for row in holdings:
    ticker = str(row.get("Ticker", "")).strip().upper()
    if ticker and ticker not in tickers:
        tickers.append(ticker)

if not tickers:
    st.info("Add holdings from the main InvestIQ page first.")
    st.stop()


selected = st.selectbox("Select a holding", tickers)


company_names = {
    "RELIANCE.NS": "Reliance Industries",
    "TCS.NS": "Tata Consultancy Services",
    "HDFCBANK.NS": "HDFC Bank",
    "INFY.NS": "Infosys",
    "ICICIBANK.NS": "ICICI Bank",
    "SBIN.NS": "State Bank of India",
    "ITC.NS": "ITC Limited",
    "BHARTIARTL.NS": "Bharti Airtel",
    "LT.NS": "Larsen & Toubro",
    "MARUTI.NS": "Maruti Suzuki",
    "TITAN.NS": "Titan Company",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "SUNPHARMA.NS": "Sun Pharma",
    "AXISBANK.NS": "Axis Bank",
    "KOTAKBANK.NS": "Kotak Mahindra Bank",
}

company = company_names.get(
    selected,
    selected.replace(".NS", "").replace(".BO", "")
)

st.markdown("### Recent Company News")


def fetch_news(company_name: str, ticker: str) -> list[dict]:
    queries = [
        f'"{company_name}" stock',
        f'"{company_name}" India business',
        ticker,
    ]

    articles = []
    seen = set()

    for query in queries:

        rss_url = (
            "https://news.google.com/rss/search?"
            f"q={quote(query)}"
            "&hl=en-IN&gl=IN&ceid=IN:en"
        )

        try:
            response = requests.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )

            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):

                title = item.findtext("title")
                link = item.findtext("link")
                pub_date = item.findtext("pubDate")
                source = item.find("source")

                publisher = (
                    source.text
                    if source is not None and source.text
                    else "News publisher"
                )

                if not title or not link:
                    continue

                key = title.strip().lower()

                if key in seen:
                    continue

                seen.add(key)

                articles.append(
                    {
                        "title": title.strip(),
                        "link": link.strip(),
                        "publisher": publisher.strip(),
                        "published": pub_date or "",
                    }
                )

                if len(articles) >= 10:
                    return articles

        except Exception:
            continue

    return articles[:10]


with st.spinner("Fetching recent company news..."):
    news = fetch_news(company, selected)


if not news:

    st.warning(
        "No recent news could be retrieved for this holding. "
        "The news provider may be temporarily unavailable."
    )

else:

    for article in news:

        st.markdown(f"#### {article['title']}")

        meta = article["publisher"]

        if article["published"]:
            try:
                parsed_date = datetime.strptime(
                    article["published"],
                    "%a, %d %b %Y %H:%M:%S %Z",
                )

                meta += " · " + parsed_date.strftime("%d %b %Y, %H:%M")

            except Exception:
                meta += f" · {article['published']}"

        st.caption(meta)

        st.link_button(
            "Read article",
            article["link"],
        )

        st.divider()


st.markdown("### How to Use This Section")

st.write(
    "Use recent news to identify company developments, announcements, "
    "business events, regulatory developments, and other information "
    "that may warrant further research."
)

st.write(
    "InvestIQ does not convert a headline into a predicted price movement "
    "or a buy, sell, or hold recommendation."
)

st.caption(
    "News source: Google News RSS search. Article links open the "
    "publisher or Google News result. Coverage and availability depend "
    "on the underlying publishers."
)
