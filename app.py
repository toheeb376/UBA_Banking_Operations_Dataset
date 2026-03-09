import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# PAGE CONFIG — must be the very first Streamlit call
# =============================================================================
st.set_page_config(
    page_title="UBA Banking Intelligence Dashboard",
    page_icon="UBA_Banking_Operations_Dataset.svg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# UBA BRAND COLOR CONSTANTS
# =============================================================================
UBA_RED   = "rgb(215,25,32)"
UBA_WHITE = "rgb(255,255,255)"
CHART_BG  = "rgb(15,15,15)"
CARD_BG   = "rgb(22,22,22)"
BORDER    = "rgb(50,50,50)"

ACCENT_COLORS = ["#D71920", "#C9A84C", "#4A90D9", "#5FAD8E", "#8A8A8A", "#E0E0E0"]

# =============================================================================
# CUSTOM CSS — Full UBA dark brand theme
# =============================================================================
st.markdown("""
<style>
    .stApp, .main, body {
        background-color: rgb(0,0,0) !important;
        color: rgb(255,255,255) !important;
    }
    section[data-testid="stSidebar"] {
        background-color: rgb(18,18,18) !important;
        border-right: 1px solid rgb(215,25,32);
    }
    section[data-testid="stSidebar"] * { color: rgb(255,255,255) !important; }
    * { color: rgb(255,255,255) !important; }
    h1 { color: rgb(215,25,32) !important; font-weight: 800 !important; }
    h2, h3 { color: rgb(215,25,32) !important; }
    div[data-testid="stMetric"] {
        background-color: rgb(22,22,22) !important;
        border-top: 3px solid rgb(215,25,32) !important;
        border: 1px solid rgb(50,50,50) !important;
        border-radius: 8px !important;
        padding: 16px 12px !important;
    }
    div[data-testid="stMetricValue"] {
        color: rgb(255,255,255) !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: rgb(180,180,180) !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .stMultiSelect > div, .stSelectbox > div,
    .stDateInput > div, div[data-baseweb="select"] {
        background-color: rgb(22,22,22) !important;
        border: 1px solid rgb(50,50,50) !important;
        border-radius: 6px !important;
    }
    .stMultiSelect [data-baseweb="tag"] {
        background-color: rgb(215,25,32) !important;
        color: rgb(255,255,255) !important;
    }
    div[data-baseweb="popover"] { background-color: rgb(22,22,22) !important; }
    li[role="option"]:hover { background-color: rgb(215,25,32) !important; }
    .stCheckbox > label { color: rgb(255,255,255) !important; }
    .streamlit-expanderHeader {
        background-color: rgb(22,22,22) !important;
        color: rgb(215,25,32) !important;
        border: 1px solid rgb(50,50,50) !important;
        border-radius: 6px !important;
        font-weight: 700;
    }
    .streamlit-expanderContent {
        background-color: rgb(14,14,14) !important;
        border: 1px solid rgb(50,50,50) !important;
        border-top: none !important;
    }
    hr { border-color: rgb(215,25,32) !important; }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgb(14,14,14); }
    ::-webkit-scrollbar-thumb { background: rgb(215,25,32); border-radius: 3px; }
    .block-container { padding-top: 1rem !important; }
    .stMarkdown p { color: rgb(200,200,200) !important; }
    .section-header {
        background: linear-gradient(90deg, rgba(215,25,32,0.12), transparent);
        border-left: 4px solid rgb(215,25,32);
        padding: 8px 16px;
        margin: 20px 0 12px 0;
        border-radius: 0 4px 4px 0;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# PLOTLY DARK LAYOUT HELPER (2D charts only)
# Uses title_font — valid for layout-level xaxis/yaxis
# =============================================================================
def dark_layout(title="", height=380):
    """Standard dark Plotly layout dict for all 2D charts."""
    return dict(
        title=dict(text=title, font=dict(color=UBA_WHITE, size=14), x=0.01),
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=UBA_WHITE, family="Arial, sans-serif", size=11),
        margin=dict(l=40, r=20, t=48, b=40),
        height=height,
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(color=UBA_WHITE)
        ),
        xaxis=dict(
            gridcolor="rgba(80,80,80,0.3)",
            linecolor=BORDER,
            tickfont=dict(color=UBA_WHITE),
            title_font=dict(color=UBA_WHITE)
        ),
        yaxis=dict(
            gridcolor="rgba(80,80,80,0.3)",
            linecolor=BORDER,
            tickfont=dict(color=UBA_WHITE),
            title_font=dict(color=UBA_WHITE)
        ),
        hoverlabel=dict(
            bgcolor=CARD_BG,
            bordercolor=UBA_RED,
            font=dict(color=UBA_WHITE)
        )
    )


# =============================================================================
# DATA LOADING & PREPROCESSING
#
# FIX 1 — pandas 2+ compatibility:
#   Do NOT use select_dtypes(include=["object","str"]) — raises TypeError.
#   Instead iterate every column and call astype(str).str.strip() individually.
# =============================================================================
@st.cache_data
def load_data():
    """Load and clean the UBA Banking Operations dataset."""
    try:
        df = pd.read_excel("UBA_Banking_Operations_Dataset.xlsx")
    except FileNotFoundError:
        st.error(
            "File not found: 'UBA_Banking_Operations_Dataset.xlsx'. "
            "Place it in the same folder as app.py and restart."
        )
        st.stop()
    except Exception as exc:
        st.error(f"Could not load dataset: {exc}")
        st.stop()

    # --- Whitespace strip: iterate every column (pandas-version safe) ---
    for col in df.columns:
        try:
            df[col] = df[col].astype(str).str.strip()
        except Exception:
            pass  # leave numeric/date columns untouched

    # --- Parse dates ---
    df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"], errors="coerce")

    # --- Parse numerics ---
    df["Amount_NGN"] = pd.to_numeric(df["Amount_NGN"], errors="coerce").fillna(0)
    df["Balance_After_Transaction_NGN"] = pd.to_numeric(
        df["Balance_After_Transaction_NGN"], errors="coerce"
    ).fillna(0)

    # --- Derived flags ---
    hv_threshold = int(df["Amount_NGN"].quantile(0.75))
    df["Is_High_Value"] = df["Amount_NGN"] >= hv_threshold
    df["Is_Successful"] = df["Transaction_Status"] == "Successful"
    df["Is_Pending"]    = df["Transaction_Status"] == "Pending"
    df["Is_Failed"]     = df["Transaction_Status"] == "Failed"

    return df, hv_threshold


df, HIGH_VALUE_THRESHOLD = load_data()


# =============================================================================
# SIDEBAR — Logo + Filters
# =============================================================================
with st.sidebar:
    # UBA Logo
    try:
        st.image("UBA_Banking_Operations_Dataset.svg", width=140)
    except Exception:
        st.markdown(
            "<h2 style='color:rgb(215,25,32);font-weight:900;'>UBA</h2>",
            unsafe_allow_html=True
        )

    st.markdown(
        "<p style='color:rgb(150,150,150);font-size:0.7rem;margin-top:-6px;'>"
        "Banking Operations Intelligence</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Date range
    st.markdown("**Date Range**")
    valid_dates = df["Transaction_Date"].dropna()
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    date_from = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    date_to   = st.date_input("To",   value=max_date, min_value=min_date, max_value=max_date)

    st.markdown("---")
    st.markdown("**Filters**")

    def make_filter(label, col):
        opts = sorted(df[col].dropna().astype(str).unique().tolist())
        return st.multiselect(label, options=opts, default=opts)

    sel_status  = make_filter("Transaction Status",  "Transaction_Status")
    sel_type    = make_filter("Transaction Type",    "Transaction_Type")
    sel_channel = make_filter("Channel",             "Channel")
    sel_region  = make_filter("Region",              "Region")
    sel_segment = make_filter("Customer Segment",    "Customer_Segment")
    sel_account = make_filter("Account Type",        "Account_Type")
    sel_product = make_filter("Product",             "Product")
    sel_branch  = make_filter("Branch",              "Branch_Name")

    st.markdown("---")
    show_high_value = st.checkbox(
        f"High-Value Only (>= N{HIGH_VALUE_THRESHOLD:,})", value=False
    )


# =============================================================================
# APPLY FILTERS
# =============================================================================
mask = (
    df["Transaction_Date"].dt.date.between(date_from, date_to)
    & df["Transaction_Status"].isin(sel_status)
    & df["Transaction_Type"].isin(sel_type)
    & df["Channel"].isin(sel_channel)
    & df["Region"].isin(sel_region)
    & df["Customer_Segment"].isin(sel_segment)
    & df["Account_Type"].isin(sel_account)
    & df["Product"].isin(sel_product)
    & df["Branch_Name"].isin(sel_branch)
)
if show_high_value:
    mask = mask & df["Is_High_Value"]

fdf = df[mask].copy()


# =============================================================================
# DASHBOARD HEADER
# =============================================================================
st.markdown(
    "<h1 style='margin-bottom:2px;'>UBA Banking Operations Intelligence</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='color:rgb(160,160,160);font-size:0.85rem;margin-top:0;'>"
    "United Bank for Africa Plc &nbsp;|&nbsp; Real-Time Transaction Analytics "
    "&nbsp;|&nbsp; Data-Driven Branch Performance</p>",
    unsafe_allow_html=True
)
st.markdown("---")


# =============================================================================
# KPI CARDS
# =============================================================================
total_txns     = len(fdf)
total_volume   = float(fdf["Amount_NGN"].sum())
avg_txn_value  = float(fdf["Amount_NGN"].mean()) if total_txns > 0 else 0.0
success_rate   = (float(fdf["Is_Successful"].sum()) / total_txns * 100) if total_txns > 0 else 0.0
pending_count  = int(fdf["Is_Pending"].sum())
failed_count   = int(fdf["Is_Failed"].sum())
high_val_count = int(fdf["Is_High_Value"].sum())
credits_sum    = float(fdf.loc[fdf["Transaction_Type"] == "Credit", "Amount_NGN"].sum())
debits_sum     = float(fdf.loc[fdf["Transaction_Type"] == "Debit",  "Amount_NGN"].sum())
net_flow       = credits_sum - debits_sum

k1, k2, k3, k4, k5, k6, k7, k8 = st.columns(8)
k1.metric("Total Transactions", f"{total_txns:,}")
k2.metric("Total Volume",       f"N{total_volume / 1e6:.2f}M")
k3.metric("Avg Transaction",    f"N{avg_txn_value:,.0f}")
k4.metric("Success Rate",       f"{success_rate:.1f}%")
k5.metric("Pending",            f"{pending_count:,}")
k6.metric("Failed",             f"{failed_count:,}")
k7.metric("High-Value",         f"{high_val_count:,}")
k8.metric("Net Flow",           f"N{net_flow / 1e6:.2f}M")

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# SECTION 1 — Transaction Overview
# =============================================================================
st.markdown(
    "<div class='section-header'><b>Transaction Overview</b></div>",
    unsafe_allow_html=True
)
col1, col2 = st.columns(2)

# Chart 1 — Status Distribution
with col1:
    s_df = fdf["Transaction_Status"].value_counts().reset_index()
    s_df.columns = ["Status", "Count"]
    s_color_map = {"Successful": "#5FAD8E", "Pending": "#C9A84C", "Failed": "#D71920"}
    fig1 = go.Figure(go.Bar(
        x=s_df["Status"].tolist(),
        y=s_df["Count"].tolist(),
        marker_color=[s_color_map.get(s, "#8A8A8A") for s in s_df["Status"]],
        text=s_df["Count"].tolist(),
        textposition="outside",
        textfont=dict(color=UBA_WHITE),
        hovertemplate="<b>%{x}</b><br>Transactions: %{y:,}<extra></extra>"
    ))
    fig1.update_layout(**dark_layout("Transaction Status Distribution"))
    st.plotly_chart(fig1, use_container_width=True)

# Chart 2 — Volume by Region (Credit vs Debit)
with col2:
    r_df = (
        fdf.groupby(["Region", "Transaction_Type"])["Amount_NGN"]
        .sum().reset_index()
    )
    t_color_map = {"Credit": "#4A90D9", "Debit": "#D71920"}
    fig2 = go.Figure()
    for txn_type, grp in r_df.groupby("Transaction_Type"):
        fig2.add_trace(go.Bar(
            x=grp["Region"].tolist(),
            y=grp["Amount_NGN"].tolist(),
            name=str(txn_type),
            marker_color=t_color_map.get(str(txn_type), "#8A8A8A"),
            hovertemplate=f"<b>%{{x}}</b><br>{txn_type}: N%{{y:,.0f}}<extra></extra>"
        ))
    fig2.update_layout(
        **dark_layout("Transaction Volume by Region (Credit vs Debit)"),
        barmode="group"
    )
    st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# SECTION 2 — Time Series + Channel Donut
# =============================================================================
col3, col4 = st.columns([3, 2])

# Chart 3 — Transactions Over Time (dual-axis)
with col3:
    dated = fdf.dropna(subset=["Transaction_Date"]).copy()
    if not dated.empty:
        ts = (
            dated.groupby(dated["Transaction_Date"].dt.date)["Amount_NGN"]
            .agg(["sum", "count"]).reset_index()
        )
        ts.columns = ["Date", "Volume", "Count"]

        fig3 = make_subplots(specs=[[{"secondary_y": True}]])
        fig3.add_trace(
            go.Scatter(
                x=ts["Date"].tolist(),
                y=ts["Volume"].tolist(),
                name="Volume (N)",
                line=dict(color="#D71920", width=2),
                fill="tozeroy",
                fillcolor="rgba(215,25,32,0.07)",
                hovertemplate="Date: %{x}<br>N%{y:,.0f}<extra></extra>"
            ),
            secondary_y=False
        )
        fig3.add_trace(
            go.Scatter(
                x=ts["Date"].tolist(),
                y=ts["Count"].tolist(),
                name="# Transactions",
                line=dict(color="#C9A84C", width=1.5, dash="dot"),
                hovertemplate="Date: %{x}<br>%{y} txns<extra></extra>"
            ),
            secondary_y=True
        )
        fig3.update_layout(**dark_layout("Transaction Activity Over Time", height=360))
        fig3.update_yaxes(
            title_text="Volume (N)", secondary_y=False,
            title_font=dict(color=UBA_WHITE),
            tickfont=dict(color=UBA_WHITE),
            gridcolor="rgba(80,80,80,0.3)"
        )
        fig3.update_yaxes(
            title_text="# Transactions", secondary_y=True,
            title_font=dict(color="#C9A84C"),
            tickfont=dict(color="#C9A84C"),
            gridcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No valid date data for the selected filters.")

# Chart 4 — Channel Usage Donut
with col4:
    ch_df = fdf["Channel"].value_counts().reset_index()
    ch_df.columns = ["Channel", "Count"]
    fig4 = go.Figure(go.Pie(
        labels=ch_df["Channel"].tolist(),
        values=ch_df["Count"].tolist(),
        hole=0.55,
        marker=dict(
            colors=ACCENT_COLORS[:len(ch_df)],
            line=dict(color=CHART_BG, width=2)
        ),
        textfont=dict(color=UBA_WHITE, size=11),
        hovertemplate="<b>%{label}</b><br>%{value:,} txns (%{percent})<extra></extra>"
    ))
    fig4.add_annotation(
        text=f"<b>{total_txns:,}</b><br>Total",
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=UBA_WHITE, size=14),
        align="center"
    )
    fig4.update_layout(**dark_layout("Channel Usage Breakdown", height=360))
    st.plotly_chart(fig4, use_container_width=True)


# =============================================================================
# SECTION 3 — Branch & Segment Performance
# =============================================================================
st.markdown(
    "<div class='section-header'><b>Branch and Segment Performance</b></div>",
    unsafe_allow_html=True
)
col5, col6 = st.columns(2)

# Chart 5 — Top Branches by Volume
with col5:
    br_df = (
        fdf.groupby("Branch_Name")["Amount_NGN"]
        .sum().sort_values(ascending=True).reset_index()
    )
    br_vals = br_df["Amount_NGN"].tolist()
    fig5 = go.Figure(go.Bar(
        x=br_vals,
        y=br_df["Branch_Name"].tolist(),
        orientation="h",
        marker=dict(
            color=br_vals,
            colorscale=[[0, "#4A0A0C"], [0.5, "#8B1014"], [1, "#D71920"]],
            showscale=False
        ),
        text=[f"N{v / 1e6:.1f}M" for v in br_vals],
        textposition="outside",
        textfont=dict(color=UBA_WHITE, size=10),
        hovertemplate="<b>%{y}</b><br>N%{x:,.0f}<extra></extra>"
    ))
    fig5.update_layout(**dark_layout("Top Branches by Transaction Volume"))
    st.plotly_chart(fig5, use_container_width=True)

# Chart 6 — Transaction Volume by Customer Segment
with col6:
    seg_df = (
        fdf.groupby("Customer_Segment")["Amount_NGN"]
        .sum().reset_index().sort_values("Amount_NGN", ascending=False)
    )
    fig6 = go.Figure(go.Bar(
        x=seg_df["Customer_Segment"].tolist(),
        y=seg_df["Amount_NGN"].tolist(),
        marker_color=ACCENT_COLORS[:len(seg_df)],
        text=[f"N{v / 1e6:.1f}M" for v in seg_df["Amount_NGN"]],
        textposition="outside",
        textfont=dict(color=UBA_WHITE, size=10),
        hovertemplate="<b>%{x}</b><br>N%{y:,.0f}<extra></extra>"
    ))
    fig6.update_layout(**dark_layout("Transaction Volume by Customer Segment"))
    st.plotly_chart(fig6, use_container_width=True)


# =============================================================================
# SECTION 4 — Product & Account Intelligence
# =============================================================================
st.markdown(
    "<div class='section-header'><b>Product and Account Intelligence</b></div>",
    unsafe_allow_html=True
)
col7, col8 = st.columns(2)

# Chart 7 — Volume by Account Type (Treemap)
with col7:
    ac_df = fdf.groupby("Account_Type")["Amount_NGN"].sum().reset_index()
    ac_df.columns = ["Account_Type", "Volume"]
    ac_vals = ac_df["Volume"].tolist()
    fig7 = go.Figure(go.Treemap(
        labels=ac_df["Account_Type"].tolist(),
        parents=[""] * len(ac_df),
        values=ac_vals,
        marker=dict(
            colors=ac_vals,
            colorscale=[[0, "#1a0405"], [0.5, "#7a1015"], [1, "#D71920"]],
            showscale=False
        ),
        textinfo="label+value",
        textfont=dict(color=UBA_WHITE, size=13),
        hovertemplate="<b>%{label}</b><br>N%{value:,.0f}<extra></extra>"
    ))
    fig7.update_layout(**dark_layout("Volume by Account Type (Treemap)"))
    st.plotly_chart(fig7, use_container_width=True)

# Chart 8 — Product Performance (dual-axis: Count + Volume)
with col8:
    pr_df = (
        fdf.groupby("Product")
        .agg(Count=("Amount_NGN", "count"), Volume=("Amount_NGN", "sum"))
        .reset_index()
        .sort_values("Count", ascending=False)
    )
    fig8 = make_subplots(specs=[[{"secondary_y": True}]])
    fig8.add_trace(
        go.Bar(
            x=pr_df["Product"].tolist(),
            y=pr_df["Count"].tolist(),
            name="# Transactions",
            marker_color="#D71920",
            hovertemplate="<b>%{x}</b><br>Count: %{y:,}<extra></extra>"
        ),
        secondary_y=False
    )
    fig8.add_trace(
        go.Scatter(
            x=pr_df["Product"].tolist(),
            y=pr_df["Volume"].tolist(),
            name="Volume (N)",
            line=dict(color="#C9A84C", width=2),
            mode="lines+markers",
            marker=dict(size=7),
            hovertemplate="<b>%{x}</b><br>N%{y:,.0f}<extra></extra>"
        ),
        secondary_y=True
    )
    fig8.update_layout(**dark_layout("Product Performance (Count and Volume)"))
    fig8.update_yaxes(
        title_text="# Transactions",
        secondary_y=False,
        gridcolor="rgba(80,80,80,0.3)",
        tickfont=dict(color=UBA_WHITE)
    )
    fig8.update_yaxes(
        title_text="Volume (N)",
        secondary_y=True,
        title_font=dict(color="#C9A84C"),
        tickfont=dict(color="#C9A84C"),
        gridcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig8, use_container_width=True)


# =============================================================================
# SECTION 5 — Flow & Credit/Debit Analysis
# =============================================================================
st.markdown(
    "<div class='section-header'><b>Flow and Credit/Debit Analysis</b></div>",
    unsafe_allow_html=True
)
col9, col10 = st.columns(2)

# Chart 9 — Credit vs Debit Donut
with col9:
    ty_df = fdf["Transaction_Type"].value_counts().reset_index()
    ty_df.columns = ["Type", "Count"]
    fig9 = go.Figure(go.Pie(
        labels=ty_df["Type"].tolist(),
        values=ty_df["Count"].tolist(),
        hole=0.45,
        marker=dict(
            colors=["#4A90D9", "#D71920"],
            line=dict(color=CHART_BG, width=2)
        ),
        textfont=dict(color=UBA_WHITE),
        hovertemplate="<b>%{label}</b><br>%{value:,} txns (%{percent})<extra></extra>"
    ))
    fig9.update_layout(**dark_layout("Credit vs. Debit Distribution", height=360))
    st.plotly_chart(fig9, use_container_width=True)

# Chart 10 — Net Cash Flow per Branch
with col10:
    pv = (
        fdf.groupby(["Branch_Name", "Transaction_Type"])["Amount_NGN"]
        .sum().unstack(fill_value=0)
    )
    if "Credit" not in pv.columns:
        pv["Credit"] = 0
    if "Debit" not in pv.columns:
        pv["Debit"] = 0
    pv["Net_Flow"] = pv["Credit"] - pv["Debit"]
    pv = pv.reset_index().sort_values("Net_Flow")
    nf_vals   = pv["Net_Flow"].tolist()
    nf_colors = ["#5FAD8E" if v >= 0 else "#D71920" for v in nf_vals]
    fig10 = go.Figure(go.Bar(
        x=nf_vals,
        y=pv["Branch_Name"].tolist(),
        orientation="h",
        marker_color=nf_colors,
        text=[f"N{v / 1e6:.2f}M" for v in nf_vals],
        textposition="outside",
        textfont=dict(color=UBA_WHITE, size=10),
        hovertemplate="<b>%{y}</b><br>Net: N%{x:,.0f}<extra></extra>"
    ))
    fig10.add_vline(x=0, line_color=UBA_WHITE, line_width=1, line_dash="dot")
    fig10.update_layout(**dark_layout("Net Cash Flow per Branch (Credit minus Debit)", height=360))
    st.plotly_chart(fig10, use_container_width=True)


# =============================================================================
# 3D INTELLIGENCE SCATTER
#
# FIX 2 — scene axis titlefont is NOT a valid Plotly property.
#   WRONG:  xaxis=dict(title="...", titlefont=dict(color="..."), ...)
#   RIGHT:  xaxis=dict(title=dict(text="...", font=dict(color="...")), ...)
#
# This fix applies to xaxis, yaxis, and zaxis inside scene=dict(...)
# =============================================================================
st.markdown(
    "<div class='section-header'><b>3D Transaction Intelligence Scatter</b></div>",
    unsafe_allow_html=True
)

sc = fdf.dropna(subset=["Amount_NGN", "Balance_After_Transaction_NGN"]).copy()
sc = sc.reset_index(drop=True)
sc["Txn_Index"] = sc.index

s3d_colors = {"Successful": "#5FAD8E", "Pending": "#C9A84C", "Failed": "#D71920"}
fig_3d = go.Figure()

for stat_val, grp in sc.groupby("Transaction_Status"):
    cd = grp[["Branch_Name", "Product", "Customer_Segment", "Channel"]].values
    fig_3d.add_trace(go.Scatter3d(
        x=grp["Amount_NGN"].tolist(),
        y=grp["Balance_After_Transaction_NGN"].tolist(),
        z=grp["Txn_Index"].tolist(),
        mode="markers",
        name=str(stat_val),
        marker=dict(
            size=4,
            color=s3d_colors.get(str(stat_val), "#8A8A8A"),
            opacity=0.82,
            line=dict(width=0)
        ),
        customdata=cd,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Product: %{customdata[1]}<br>"
            "Segment: %{customdata[2]}<br>"
            "Channel: %{customdata[3]}<br>"
            "Amount: N%{x:,.0f}<br>"
            "Balance After: N%{y:,.0f}<extra></extra>"
        )
    ))

# ── CORRECT 3D scene axis syntax ────────────────────────────────────────────
# Use title=dict(text="...", font=dict(...)) NOT titlefont=dict(...)
# titlefont is a DEPRECATED alias that raises ValueError in Plotly 5+
# ─────────────────────────────────────────────────────────────────────────────
fig_3d.update_layout(
    paper_bgcolor=CHART_BG,
    height=540,
    margin=dict(l=0, r=0, t=50, b=0),
    title=dict(
        text="3D Scatter: Amount x Balance After x Sequence  |  Colour = Status",
        font=dict(color=UBA_WHITE, size=13),
        x=0.01
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(color=UBA_WHITE)
    ),
    hoverlabel=dict(
        bgcolor=CARD_BG,
        bordercolor=UBA_RED,
        font=dict(color=UBA_WHITE)
    ),
    scene=dict(
        bgcolor=CHART_BG,
        # FIXED: title=dict(text=..., font=dict(...)) — NOT titlefont=dict(...)
        xaxis=dict(
            title=dict(
                text="Amount (N)",
                font=dict(color=UBA_WHITE, size=11)
            ),
            tickfont=dict(color=UBA_WHITE),
            gridcolor="rgba(80,80,80,0.4)",
            backgroundcolor=CHART_BG,
            showbackground=True
        ),
        yaxis=dict(
            title=dict(
                text="Balance After (N)",
                font=dict(color=UBA_WHITE, size=11)
            ),
            tickfont=dict(color=UBA_WHITE),
            gridcolor="rgba(80,80,80,0.4)",
            backgroundcolor=CHART_BG,
            showbackground=True
        ),
        zaxis=dict(
            title=dict(
                text="Transaction Sequence",
                font=dict(color=UBA_WHITE, size=11)
            ),
            tickfont=dict(color=UBA_WHITE),
            gridcolor="rgba(215,25,32,0.2)",
            backgroundcolor=CHART_BG,
            showbackground=True
        )
    )
)
st.plotly_chart(fig_3d, use_container_width=True)


# =============================================================================
# EXECUTIVE INSIGHT PANEL
# =============================================================================
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("Executive Intelligence Summary - Click to Expand", expanded=False):
    st.markdown("""
    <div style='padding:12px 8px; color:rgb(200,200,200); line-height:1.8;'>

    <h4 style='color:rgb(215,25,32);'>Transaction Success Rate and Channel Reliability</h4>
    <p>The <b>Transaction Success Rate</b> is the single most critical operational KPI. A rate below 90%
    signals issues with channel uptime, network reliability, or fraud rejection policies. Drill into
    <b>Channel</b> and <b>Branch</b> filters to isolate underperforming touchpoints. POS and ATM failures
    often indicate hardware or connectivity issues; Mobile App failures may point to API or session
    timeout problems.</p>

    <h4 style='color:rgb(215,25,32);'>Regional and Branch Volume Disparities</h4>
    <p>Transaction volumes heavily concentrated in one or two branches while others show low throughput
    can indicate unequal resource allocation, customer acquisition gaps, or geographic market maturity
    differences. Operations teams should benchmark low-volume branches against high-volume peers for
    staffing, product mix, and marketing strategy.</p>

    <h4 style='color:rgb(215,25,32);'>Pending Transactions and Cash Flow Risk</h4>
    <p>A rising <b>Pending count</b> is an early warning indicator of processing bottlenecks, failed
    settlement windows, or core banking system delays. Finance teams should monitor this daily. Immediate
    escalation to IT and settlement operations is warranted if the pending rate exceeds 10%.</p>

    <h4 style='color:rgb(215,25,32);'>Credit vs. Debit Net Flow per Branch</h4>
    <p>Branches with consistently <b>negative net flow</b> (Debits greater than Credits) are net liquidity
    outflows and may require more frequent ATM cash replenishment or tighter withdrawal controls. Branches
    with high positive net flow are accumulating deposits, signalling cross-selling or treasury reallocation
    opportunities.</p>

    <h4 style='color:rgb(215,25,32);'>High-Value Transaction Monitoring</h4>
    <p>Transactions in the top 25th percentile carry elevated compliance and AML scrutiny under CBN
    guidelines. Risk and compliance teams should review the <b>High-Value</b> filter daily to ensure
    proper documentation, approval workflows, and suspicious transaction reporting (STR) are in place.</p>

    <h4 style='color:rgb(215,25,32);'>Product Performance and Revenue Mix</h4>
    <p>Tracking which products (Money Transfer, Loan Repayment, Bill Payment, etc.) drive the most
    transaction volume allows product managers to optimise fee structures. Declining Loan Repayment
    volumes may signal NPL (Non-Performing Loan) risk and should be escalated to the credit risk team.</p>

    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; padding:12px; color:rgb(100,100,100); font-size:0.72rem;'>"
    f"<span style='color:rgb(215,25,32);font-weight:700;'>UBA</span> "
    f"Banking Operations Intelligence &nbsp;|&nbsp; "
    f"United Bank for Africa Plc &nbsp;|&nbsp; "
    f"Python &middot; Streamlit &middot; Plotly &nbsp;|&nbsp; "
    f"Dataset: {len(df):,} records &nbsp;&middot;&nbsp; Filtered: {len(fdf):,} records"
    f"</div>",
    unsafe_allow_html=True
)
