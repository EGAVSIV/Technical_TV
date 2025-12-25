import streamlit as st
import pandas as pd
from tradingview_screener import Query, Column as col
from typing import Optional
import io
import requests

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="📉 Indian Technical Stock Screener",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Indian Stock Technical Screener")
st.caption("Powered by TradingView Technical Data | NSE + BSE")

# ==================================================
# SIDEBAR – PRESETS
# ==================================================
PRESETS = {
    "None": None,
    "Top Gainers": "gainers",
    "Biggest Losers": "losers",
    "Most Active": "most_active",
    "Unusual Volume": "unusual_volume",
    "Overbought (RSI > 70)": "overbought",
    "Oversold (RSI < 30)": "oversold",
}

st.sidebar.header("📌 Preset Filters")
preset_label = st.sidebar.selectbox("Select Preset", PRESETS.keys())
preset_value = PRESETS[preset_label]

# ==================================================
# TECHNICAL FILTERS
# ==================================================
st.sidebar.header("📉 Technical Filters")

min_rsi = st.sidebar.slider("Min RSI", 0, 100, 40)
max_rsi = st.sidebar.slider("Max RSI", 0, 100, 70)

price_above_ema20 = st.sidebar.checkbox("Price Above EMA 20", True)
price_above_ema50 = st.sidebar.checkbox("Price Above EMA 50", True)
price_above_ema200 = st.sidebar.checkbox("Price Above EMA 200", False)

min_volume = st.sidebar.number_input("Min Volume", min_value=0, value=100000)

limit = st.sidebar.slider("Number of Stocks", 10, 200, 50)

run_scan = st.sidebar.button("🚀 Run Technical Screener")

# ==================================================
# SAFE TECHNICAL SCREENER FUNCTION
# ==================================================
def run_technical_scan(preset: Optional[str]) -> pd.DataFrame:
    try:
        q = (
            Query()
            .set_markets("india")
            .select(
                "name",
                "sector",
                "close",
                "change",
                "volume",
                "RSI",
                "EMA20",
                "EMA50",
                "EMA200",
                "MACD.macd",
                "MACD.signal",
            )
            .where(
                col("type") == "stock",
                col("typespecs").has("common"),
                col("is_primary") == True,
                col("RSI") >= min_rsi,
                col("RSI") <= max_rsi,
                col("volume") >= min_volume,
            )
            .limit(limit)
        )

        if price_above_ema20:
            q = q.where(col("close") > col("EMA20"))
        if price_above_ema50:
            q = q.where(col("close") > col("EMA50"))
        if price_above_ema200:
            q = q.where(col("close") > col("EMA200"))

        if preset:
            q = q.set_property("preset", preset)

        _, df = q.get_scanner_data(timeout=30)
        return df

    except requests.exceptions.HTTPError:
        st.error("TradingView rejected the request. Reduce filters or stock count.")
        return pd.DataFrame()

    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame()

# ==================================================
# MAIN OUTPUT
# ==================================================
if run_scan:

    with st.spinner("Scanning Indian Markets (Technical)..."):
        df = run_technical_scan(preset_value)

    if df.empty:
        st.warning("No stocks matched the technical criteria.")
    else:
        df["MACD Trend"] = df["MACD.macd"] - df["MACD.signal"]

        display_cols = [
            "name",
            "sector",
            "close",
            "change",
            "volume",
            "RSI",
            "EMA20",
            "EMA50",
            "EMA200",
            "MACD Trend",
        ]

        st.subheader(f"📋 Technical Screener Results ({len(df)} stocks)")

        st.dataframe(
            df[display_cols].sort_values("RSI", ascending=False),
            use_container_width=True
        )

        # =========================
        # EXPORT TO EXCEL
        # =========================
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Technical")

        st.download_button(
            label="⬇️ Download Excel",
            data=output.getvalue(),
            file_name="india_technical_screener.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ==================================================
# FOOTER
# ==================================================
st.markdown("---")
st.markdown(
    """
**Designed by Gaurav**  
📈 Technical • Quant • Price Action Intelligence  
Built with ❤️ using TradingView data
"""
)
