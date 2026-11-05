from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="The Invisible Workforce | Lebanon",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

LFS_FILE = DATA_DIR / "Labour-force-FULFS-2022.xlsx"

# ============================================================
# 2. COLORS AND CHART SETTINGS
# ============================================================

COLORS = {
    "Women": "#D96C5F",
    "Men": "#087E8B",
    "Women & Men": "#D7A84B"
}

STATUS_COLORS = {
    "Employed": "#087E8B",
    "Unemployed": "#D7A84B",
    "Outside labour force": "#D96C5F"
}

PLOT_LAYOUT = {
    "template": "plotly_white",
    "font": {
        "family": "Arial",
        "color": "#172A3A"
    },
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {
        "l": 25,
        "r": 25,
        "t": 65,
        "b": 45
    },
    "legend_title_text": ""
}

# ============================================================
# 3. PAGE STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F7F8F6;
    }
    .block-container {
        max-width: 1250px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    .hero {
        background: linear-gradient(120deg, #122B3A, #1E5260);
        padding: 2.4rem;
        border-radius: 18px;
        color: white;
        margin-bottom: 1.4rem;
    }
    .hero h1 {
        color: white;
        font-size: 3rem;
        line-height: 1.1;
        margin-bottom: .6rem;
    }
    .hero p {
        color: #E6F0F0;
        font-size: 1.08rem;
    }
    .insight {
        background: white;
        border-left: 4px solid #087E8B;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin: .7rem 0 1rem 0;
    }
    .small-note {
        color: #657786;
        font-size: .88rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 4. HISTORICAL UNEMPLOYMENT DATA
# ============================================================

@st.cache_data
def load_historical_data():
    years = list(range(1991, 2024))
    total = [
        8.554, 8.225, 8.225, 8.321, 8.421, 8.413,
        8.662, 8.571, 8.677, 8.641, 8.459, 8.248,
        8.061, 7.850, 8.249, 8.679, 8.980, 7.666,
        6.355, 6.768, 7.352, 7.952, 8.477, 8.841,
        9.312, 9.794, 10.258, 10.755, 11.301,
        13.252, 12.715, 11.105, 10.985
    ]
    female = [
        10.553, 8.812, 10.171, 10.256, 10.346,
        10.328, 10.524, 10.437, 10.602, 10.462,
        10.125, 9.373, 9.755, 9.572, 9.742,
        9.999, 10.242, 10.399, 10.345, 10.671,
        11.210, 11.753, 12.195, 12.445, 12.812,
        13.176, 13.520, 13.898, 14.323, 16.249,
        15.874, 14.593, 14.480
    ]
    male = [
        8.080, 7.694, 7.688, 7.778, 7.784,
        7.857, 8.066, 8.024, 8.254, 8.116,
        7.979, 7.732, 7.755, 7.342, 7.784,
        8.258, 8.602, 6.790, 4.999, 5.409,
        5.978, 6.568, 7.094, 7.468, 7.941,
        8.418, 8.880, 9.376, 9.392, 12.045,
        11.515, 9.816, 9.705
    ]
    historical_df = pd.DataFrame({
        "Year": years,
        "Total unemployment": total,
        "Female unemployment": female,
        "Male unemployment": male
    })
    return historical_df

# ============================================================
# 5. GENERAL SURVEY HELPER FUNCTION
# ============================================================
def read_section(sheet_name, start_row, end_row):
    raw = pd.read_excel(
        LFS_FILE,
        sheet_name=sheet_name,
        header=None,
        engine="openpyxl"
    )
    table = raw.iloc[start_row:end_row, 0:4].copy()
    table.columns = [
        "Category",
        "Women",
        "Men",
        "Women & Men"
    ]
    table["Category"] = table["Category"].astype(str).str.strip()
    
    for column in ["Women", "Men", "Women & Men"]:
        table[column] = pd.to_numeric(table[column], errors="coerce")

    table = table.dropna(subset=["Women", "Men"])
    table = table[~table["Category"].str.lower().isin(["", "nan", "total"])]
    
    return table.reset_index(drop=True)

# ============================================================
# 6. LOAD THE 2022 LABOUR FORCE SURVEY
# ============================================================

@st.cache_data
def load_survey():
    if not LFS_FILE.exists():
        raise FileNotFoundError(f"Survey workbook not found: {LFS_FILE}")

    headline_raw = pd.read_excel(
        LFS_FILE,
        sheet_name="EA1",
        header=None,
        engine="openpyxl"
    )

    headline_dict = {}

    for row_index in range(6, 12):
        label = str(headline_raw.iloc[row_index, 0]).strip()
        if label == "" or label.lower() == "nan":
            continue

        headline_dict[label] = {
            "Women": pd.to_numeric(headline_raw.iloc[row_index, 1], errors="coerce"),
            "Men": pd.to_numeric(headline_raw.iloc[row_index, 2], errors="coerce"),
            "Women & Men": pd.to_numeric(headline_raw.iloc[row_index, 3], errors="coerce")
        }

    age_lfp_df = read_section("EA40", 6, 17)
    education_lfp_df = read_section("EA40", 18, 25)
    age_unemployment_df = read_section("EA39", 6, 17)
    education_unemployment_df = read_section("EA39", 18, 25)
    employed_education_df = read_section("EA6", 6, 13)
    employment_status_df = read_section("EA8", 7, 12)
    job_search_df = read_section("EA37", 7, 12)

    status_raw = pd.read_excel(
        LFS_FILE,
        sheet_name="EA3",
        header=None,
        engine="openpyxl"
    )

    status_df = status_raw.iloc[16:18, 0:4].copy()
    status_df.columns = [
        "Gender",
        "Employed",
        "Unemployed",
        "Outside labour force"
    ]
    status_df["Gender"] = status_df["Gender"].astype(str).str.strip()

    for column in ["Employed", "Unemployed", "Outside labour force"]:
        status_df[column] = pd.to_numeric(status_df[column], errors="coerce")

    status_df = status_df.dropna(subset=["Employed", "Unemployed"])

    return (
        headline_dict,
        age_lfp_df,
        education_lfp_df,
        age_unemployment_df,
        education_unemployment_df,
        employed_education_df,
        employment_status_df,
        job_search_df,
        status_df
    )

# ============================================================
# 7. FIND HEADLINE INDICATORS
# ============================================================

def find_indicator(headline_dict, keyword):
    for label, values in headline_dict.items():
        if keyword.lower() in label.lower():
            return values
    return {
        "Women": float("nan"),
        "Men": float("nan"),
        "Women & Men": float("nan")
    }

# ============================================================
# 8. LOAD DATA
# ============================================================

try:
    historical = load_historical_data()
    (
        headline,
        age_lfp,
        education_lfp,
        age_unemployment,
        education_unemployment,
        employed_education,
        employment_status,
        job_search,
        status_by_gender
    )
    = load_survey()
except Exception as error:
    st.error(
        "The dashboard could not load the data. "
        "Please check the Excel filename and sheet structure."
    )
    st.exception(error)
    st.stop()

# ============================================================
# 9. PREPARE HEADLINE VALUES
# ============================================================

lfp = find_indicator(headline, "participation")
unemployment = find_indicator(headline, "unemployment rate")
participation_gap = lfp["Men"] - lfp["Women"]

# ============================================================
# 10. DASHBOARD HEADER
# ============================================================

st.markdown(
    """
    <div class="hero">
        <div style="letter-spacing:.14em; text-transform:uppercase; font-size:.75rem; color:#9DD4D3; font-weight:700;">
            Lebanon · Labour Market · 2022
        </div>
        <h1>The Invisible Workforce</h1>
        <p>
            <b>Understanding gender, education and paid employment in Lebanon.</b><br>
            Explore how labour-force participation and unemployment differ between women and men, and how these patterns vary by age and education.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

st.write(
    "This interactive dashboard explores labour-force "
    "participation, unemployment, age patterns and "
    "education outcomes using Lebanon's Labour Force "
    "and Household Living Conditions Survey."
)

# ============================================================
# 11. HEADLINE INDICATORS
# ============================================================

st.subheader("The Headline Indicators")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Women's Participation", f"{lfp['Women']:.1f}%")
k2.metric("Men's Participation", f"{lfp['Men']:.1f}%")
k3.metric("Participation Gap", f"{participation_gap:.1f} pp")
k4.metric("Women's Unemployment", f"{unemployment['Women']:.1f}%")

st.markdown(
    f"""
    <div class="insight">
    <b>Key Observation:</b><br><br>
    Women participate in the labour force at <strong>{lfp['Women']:.1f}%</strong>.<br>
    Men participate at <strong>{lfp['Men']:.1f}%</strong>.<br>
    The gap is <strong>{participation_gap:.1f}</strong> percentage points.
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 12. DASHBOARD TABS
# ============================================================

story_tab, explore_tab, findings_tab, action_tab, methods_tab = st.tabs([
    "The Story",
    "Explore Data",
    "Key Findings",
    "From Evidence To Action",
    "Methodology & Sources"
])

# ============================================================
# 13. THE STORY TAB
# ============================================================

with story_tab:
    st.header("The Question Behind The Numbers")
    st.write("How are gender, education and age associated with labour-force participation in Lebanon?")
    st.write("The dashboard focuses on labour-market relationships observable in the available survey tables.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Participation\nWho is employed, unemployed, or outside the labour force?")
    with col2:
        st.markdown("### Education\nHow do education levels relate to labour outcomes?")
    with col3:
        st.markdown("### Age\nAt which ages are gender differences most visible?")

    st.info("The survey is cross-sectional and does not establish causality.")

# ============================================================
# 14. EXPLORE THE DATA TAB
# ============================================================

with explore_tab:
    st.header("Explore the Labour-Market Landscape")
    st.caption("Hover over charts for exact values.")

    # CHART 1
    st.subheader("1. Unemployment Over Time")
    historical_long = historical.melt(
        id_vars="Year",
        value_vars=["Total unemployment", "Female unemployment", "Male unemployment"],
        var_name="Indicator",
        value_name="Rate"
    )

    historical_colors = {
        "Total unemployment": "#D7A84B",
        "Female unemployment": "#D96C5F",
        "Male unemployment": "#087E8B"
    }

    fig1 = px.line(
        historical_long,
        x="Year",
        y="Rate",
        color="Indicator",
        markers=True,
        color_discrete_map=historical_colors
    )
    fig1.update_layout(**PLOT_LAYOUT, hovermode="x unified")
    st.plotly_chart(fig1, use_container_width=True)

    # CHART 2
    st.subheader("2. Unemployment by Gender")
    gender_unemployment = pd.DataFrame({
        "Gender": ["Women", "Men"],
        "Rate": [unemployment["Women"], unemployment["Men"]]
    })

    fig2 = px.bar(
        gender_unemployment,
        x="Gender",
        y="Rate",
        color="Gender",
        text_auto=".1f",
        color_discrete_map=COLORS
    )
    fig2.update_layout(**PLOT_LAYOUT, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    # CHART 3
    st.subheader("3. Unemployment by Age")
    age_unemployment_long = age_unemployment.melt(
        id_vars="Category",
        value_vars=["Women", "Men"],
        var_name="Gender",
        value_name="Unemployment"
    )

    fig3 = px.line(
        age_unemployment_long,
        x="Category",
        y="Unemployment",
        color="Gender",
        markers=True,
        color_discrete_map=COLORS
    )
    fig3.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig3, use_container_width=True)

    # CHART 4
    st.subheader("4. Participation by Age")
    age_options = age_lfp["Category"].tolist()
    chosen_ages = st.multiselect("Select age groups", options=age_options, default=age_options)

    age_view = age_lfp[age_lfp["Category"].isin(chosen_ages)]
    age_long = age_view.melt(
        id_vars="Category",
        value_vars=["Women", "Men"],
        var_name="Gender",
        value_name="Participation"
    )

    fig4 = px.line(
        age_long,
        x="Category",
        y="Participation",
        color="Gender",
        markers=True,
        color_discrete_map=COLORS
    )
    fig4.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

    # CHART 5
    st.subheader("5. Participation by Education")
    education_options = education_lfp["Category"].tolist()
    chosen_education = st.multiselect("Select education levels", options=education_options, default=education_options)

    education_view = education_lfp[education_lfp["Category"].isin(chosen_education)]
    education_long = education_view.melt(
        id_vars="Category",
        value_vars=["Women", "Men"],
        var_name="Gender",
        value_name="Participation"
    )

    fig5 = px.bar(
        education_long,
        x="Category",
        y="Participation",
        color="Gender",
        barmode="group",
        color_discrete_map=COLORS
    )
    fig5.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig5, use_container_width=True)

    with st.expander("View the Tables Used in the Charts"):
        st.dataframe(age_lfp, use_container_width=True)
        st.dataframe(education_lfp, use_container_width=True)
        st.dataframe(education_unemployment, use_container_width=True)
        st.download_button(
            label="Download Participation Data",
            data=education_lfp.to_csv(index=False).encode("utf-8-sig"),
            file_name="participation.csv",
            mime="text/csv"
        )

# ============================================================
# 15. KEY FINDINGS TAB
# ============================================================

with findings_tab:
    st.header("What Does the Evidence Suggest?")
    st.write("These findings summarize patterns observed in the survey tables. They do not establish causality.")

    # FINDING A
    st.subheader("A. Education and Participation")
    education_gap = education_lfp.copy()
    education_gap["Gender Gap"] = education_gap["Men"] - education_gap["Women"]

    edu_finding_long = education_gap.melt(
        id_vars=["Category", "Gender Gap"],
        value_vars=["Women", "Men"],
        var_name="Gender",
        value_name="Participation"
    )

    fig_a = px.bar(
        edu_finding_long,
        x="Category",
        y="Participation",
        color="Gender",
        barmode="group",
        color_discrete_map=COLORS
    )
    fig_a.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_a, use_container_width=True)

    university = education_lfp[
        education_lfp["Category"].astype(str).str.lower().str.contains("university", na=False)
    ]

    if not university.empty:
        women_rate = university.iloc[0]["Women"]
        men_rate = university.iloc[0]["Men"]
        st.markdown(
            f"""
            <div class="insight">
            <b>University Education</b><br><br>
            Women: <strong>{women_rate:.1f}%</strong><br>
            Men: <strong>{men_rate:.1f}%</strong><br>
            Gap: <strong>{men_rate - women_rate:.1f} percentage points</strong>
            </div>
            """,
            unsafe_allow_html=True
        )

    # FINDING B
    st.subheader("B. Participation Gap by Age")
    age_gap = age_lfp.copy()
    age_gap["Gap"] = age_gap["Men"] - age_gap["Women"]

    fig_b = px.bar(
        age_gap,
        x="Category",
        y="Gap",
        color="Gap",
        color_continuous_scale=["#F2C7BF", "#D96C5F"]
    )
    fig_b.update_layout(**PLOT_LAYOUT, coloraxis_showscale=False)
    st.plotly_chart(fig_b, use_container_width=True)

    # FINDING C
    st.subheader("C. Economic Status")
    status_long = status_by_gender.melt(
        id_vars="Gender",
        value_vars=["Employed", "Unemployed", "Outside labour force"],
        var_name="Status",
        value_name="Share"
    )

    fig_c = px.bar(
        status_long,
        x="Gender",
        y="Share",
        color="Status",
        barmode="stack",
        color_discrete_map=STATUS_COLORS
    )
    fig_c.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_c, use_container_width=True)

    # FINDING E
    st.subheader("E. Unemployment by Education")
    unemployment_long = education_unemployment.melt(
        id_vars="Category",
        value_vars=["Women", "Men"],
        var_name="Gender",
        value_name="Unemployment"
    )

    fig_e = px.bar(
        unemployment_long,
        x="Category",
        y="Unemployment",
        color="Gender",
        barmode="group",
        color_discrete_map=COLORS
    )
    fig_e.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_e, use_container_width=True)

    st.warning(
        "The available survey tables do not provide "
        "marital status or household composition "
        "cross-tabulations. Further analysis would require "
        "additional microdata."
    )

# ============================================================
# 16. FROM EVIDENCE TO ACTION TAB
# ============================================================

with action_tab:
    st.header("From Evidence to Action")
    st.write("These recommendations are informed by patterns in the data. They should be evaluated before implementation.")

    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            ### 1 · Education-to-Employment Bridge
            Strengthen:
            - Career guidance
            - Internships
            - Apprenticeships
            - Employer partnerships
            to improve transitions from education into employment.
            """
        )
        st.markdown(
            """
            ### 2 · Work and Care Support
            Evaluate the role of:
            - Childcare
            - Transport access
            - Flexible work arrangements
            in supporting labour-force participation.
            """
        )
    with right:
        st.markdown(
            """
            ### 3 · Return-to-Work Pathways
            Support labour-market re-entry through:
            - Skills refresh programmes
            - Professional mentoring
            - Job placement support
            - Digital skills training
            """
        )
        st.markdown(
            """
            ### 4 · Measure Opportunity
            Track:
            - Recruitment
            - Promotion
            - Earnings
            - Employment conditions
            across gender and education groups.
            """
        )

    st.info("Effective policy should focus on both participation barriers and employment quality.")

# ============================================================
# 17. METHODOLOGY AND SOURCES
# ============================================================

with methods_tab:
    st.header("Methodology and Sources")
    st.markdown(
        """
        **National Source**
        Lebanon Labour Force and Household Living Conditions Survey (2022).
        Tables used:
        - EA1
        - EA3
        - EA6
        - EA8
        - EA37
        - EA39
        - EA40
        """
    )
    st.markdown(
        """
        **Historical Source**
        Historical unemployment estimates covering 1991–2023.
        Includes:
        - Total unemployment
        - Female unemployment
        - Male unemployment
        """
    )
    st.markdown(
        """
        **Analytical Approach**
        This dashboard presents:
        - Labour-force participation
        - Unemployment
        - Education outcomes
        - Employment composition
        - Job-search behaviour
        using descriptive statistics.
        """
    )
    st.markdown(
        """
        **Limitations**
        - Cross-sectional survey
        - No causal interpretation
        - Limited household variables
        - No marital-status cross-tabulations
        - No household-composition cross-tabulations
        """
    )
    st.markdown(
        """
        **Definitions**
        Labour-force participation: employed + unemployed persons relative to the population.
        Unemployment: share of the labour force that is not currently employed.
        Outside labour force: neither employed nor unemployed.
        """
    )

# ============================================================
# 18. FOOTER
# ============================================================

st.markdown("---")
st.caption(
    "The Invisible Workforce · Lebanon\n\n"
    "Interactive Labour Market Dashboard\n\n"
    "Based on the Labour Force and Household Living Conditions Survey 2022"
)
