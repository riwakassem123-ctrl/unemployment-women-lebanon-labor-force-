from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="The Invisible Workforce | Lebanon", page_icon="📊", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LFS_FILE = DATA_DIR / "Labour-force-FULFS-2022.xlsx"
WB_TOTAL_FILE = DATA_DIR / "worldbank_total_unemployment.xlsx"
WB_MALE_FILE = DATA_DIR / "worldbank_male_unemployment.xlsx"

COLORS = {"Women": "#D96C5F", "Men": "#087E8B", "Women & Men": "#D7A84B"}
PLOT_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Arial", "color": "#172A3A"},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": {"l": 20, "r": 20, "t": 60, "b": 35},
    "legend_title_text": "",
}

st.markdown("""
<style>
.stApp {background:#F7F8F6;}
.block-container {max-width:1250px;padding-top:2rem;padding-bottom:3rem;}
.hero {background:linear-gradient(120deg,#122B3A,#1E5260);padding:2.4rem;border-radius:18px;color:white;margin-bottom:1.4rem;}
.hero h1 {color:white;font-size:3rem;line-height:1.1;margin-bottom:.6rem;}
.hero p {color:#E6F0F0;font-size:1.08rem;}
.insight {background:white;border-left:4px solid #087E8B;padding:1rem 1.2rem;border-radius:8px;margin:.7rem 0 1rem 0;}
.small-note {color:#657786;font-size:.88rem;}
</style>
""", unsafe_allow_html=True)


def read_section(sheet_name, start_row, end_row):
    """Read columns A:D from a known section of the national survey workbook."""
    raw = pd.read_excel(LFS_FILE, sheet_name=sheet_name, header=None)
    table = raw.iloc[start_row:end_row, 0:4].copy()
    table.columns = ["Category", "Women", "Men", "Women & Men"]
    table["Category"] = table["Category"].astype(str).str.strip()
    for col in ["Women", "Men", "Women & Men"]:
        table[col] = pd.to_numeric(table[col], errors="coerce")
    table = table.dropna(subset=["Women", "Men"])
    table = table[~table["Category"].isin(["", "nan", "Total"])]
    return table


@st.cache_data(show_spinner=False)
def load_survey():
    if not LFS_FILE.exists():
        raise FileNotFoundError(f"Missing survey file: {LFS_FILE}")

    headline_raw = pd.read_excel(LFS_FILE, sheet_name="EA1", header=None)
    headline = {}
    for row_index in range(6, 12):
        label = str(headline_raw.iloc[row_index, 0]).strip()
        headline[label] = {
            "Women": pd.to_numeric(headline_raw.iloc[row_index, 1], errors="coerce"),
            "Men": pd.to_numeric(headline_raw.iloc[row_index, 2], errors="coerce"),
            "Women & Men": pd.to_numeric(headline_raw.iloc[row_index, 3], errors="coerce"),
        }

    age_lfp = read_section("EA40", 6, 17)
    education_lfp = read_section("EA40", 18, 25)
    age_unemployment = read_section("EA39", 6, 17)
    education_unemployment = read_section("EA39", 18, 25)
    employed_education = read_section("EA6", 6, 13)
    employment_status = read_section("EA8", 7, 12)
    job_search = read_section("EA37", 7, 12)

    status_raw = pd.read_excel(LFS_FILE, sheet_name="EA3", header=None)
    status = status_raw.iloc[16:18, 0:4].copy()
    status.columns = ["Gender", "Employed", "Unemployed", "Outside labour force"]
    for col in ["Employed", "Unemployed", "Outside labour force"]:
        status[col] = pd.to_numeric(status[col], errors="coerce")

    return (headline, age_lfp, education_lfp, age_unemployment,
            education_unemployment, employed_education, employment_status,
            job_search, status)


@st.cache_data(show_spinner=False)
def load_world_bank(file_path, label):
    if not file_path.exists():
        return pd.DataFrame()
    raw = pd.read_excel(file_path, sheet_name="Data", header=3)
    if "Country Name" not in raw.columns:
        return pd.DataFrame()
    country = raw[raw["Country Name"].astype(str).str.strip().eq("Lebanon")]
    if country.empty:
        return pd.DataFrame()
    row = country.iloc[0]
    year_columns = [col for col in raw.columns if str(col).replace(".0", "").isdigit()]
    result = pd.DataFrame({
        "Year": [int(float(col)) for col in year_columns],
        "Rate": [pd.to_numeric(row[col], errors="coerce") for col in year_columns],
    }).dropna(subset=["Rate"])
    result["Indicator"] = label
    return result


try:
    (headline, age_lfp, education_lfp, age_unemployment,
     education_unemployment, employed_education, employment_status,
     job_search, status_by_gender) = load_survey()
    wb_total = load_world_bank(WB_TOTAL_FILE, "Total unemployment")
    wb_male = load_world_bank(WB_MALE_FILE, "Male unemployment")
except Exception as error:
    st.error("The dashboard could not load the datasets. Check the filenames and Excel sheets in the data folder.")
    st.exception(error)
    st.stop()

lfp = headline.get("Labour Force Participation Rate", {})
unemployment = headline.get("LU1: Unemployment rate", {})
participation_gap = lfp.get("Men", float("nan")) - lfp.get("Women", float("nan"))

st.markdown("""
<div class="hero">
  <div style="letter-spacing:.14em;text-transform:uppercase;font-size:.75rem;color:#9DD4D3;font-weight:700;">Lebanon · Labour market · 2022</div>
  <h1>The Invisible Workforce</h1>
  <p><b>Understanding gender, education and paid employment in Lebanon.</b><br>
  Explore how labour-force participation and unemployment differ between women and men, and how these patterns vary by age and education.</p>
</div>
""", unsafe_allow_html=True)

st.write("This interactive research blog uses Lebanon's 2022 Labour Force and Household Living Conditions Survey, alongside World Bank unemployment estimates, to explore gender differences in the labour market.")

st.subheader("The headline indicators")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Women's labour-force participation", f"{lfp.get('Women', float('nan')):.1f}%")
k2.metric("Men's labour-force participation", f"{lfp.get('Men', float('nan')):.1f}%")
k3.metric("Participation gap", f"{participation_gap:.1f} pp")
k4.metric("Women's unemployment rate", f"{unemployment.get('Women', float('nan')):.1f}%")
st.markdown(
    f'<div class="insight"><b>Key observation:</b> In the 2022 survey, labour-force participation was '
    f'{lfp.get("Women", float("nan")):.1f}% for women and {lfp.get("Men", float("nan")):.1f}% for men. '
    f'The difference is {participation_gap:.1f} percentage points. Unemployment alone does not capture '
    'the full picture because people outside the labour force are not counted as unemployed.</div>',
    unsafe_allow_html=True,
)

story_tab, explore_tab, findings_tab, action_tab, methods_tab = st.tabs([
    "The story", "Explore the data", "Key findings", "From evidence to action", "Methodology & sources"
])

with story_tab:
    st.header("The question behind the numbers")
    st.write("How are gender, educational attainment and age associated with paid labour participation in Lebanon, and do these relationships differ between women and men?")
    st.write("The dashboard focuses on the variables supported by the uploaded national tables. Marital status and household composition are not included in the available cross-tabulations, so no conclusions are drawn about them.")
    a, b, c = st.columns(3)
    a.markdown("### 01 · Participation\nWho is employed, unemployed or outside the labour force?")
    b.markdown("### 02 · Education\nHow do participation and unemployment vary by completed education?")
    c.markdown("### 03 · Age\nAt which life stages are the gender differences most visible?")
    st.info("The 2022 survey is a cross-sectional snapshot. It shows associations and differences, not causal effects.")

with explore_tab:
    st.header("Explore the labour-market landscape")
    st.caption("Hover over the charts for exact values. Use the filters to focus on selected age groups and education levels.")

    st.subheader("1. Unemployment over time")
    if not wb_total.empty or not wb_male.empty:
        trend = pd.concat([wb_total, wb_male], ignore_index=True)
        fig = px.line(trend, x="Year", y="Rate", color="Indicator", markers=True,
                      color_discrete_map={"Total unemployment": "#D7A84B", "Male unemployment": "#087E8B"},
                      title="World Bank modelled ILO unemployment estimates for Lebanon",
                      labels={"Rate": "Unemployment rate (%)", "Year": "Year"})
        fig.update_layout(**PLOT_LAYOUT, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("The supplied World Bank files contain total and male series. The female comparison for 2022 comes from the national labour-force survey below; no historical female series is inferred.")
    else:
        st.warning("World Bank time-series files are missing. Upload both World Bank workbooks to the data folder to display this chart.")

    st.subheader("2. Unemployment by gender in 2022")
    gender_unemployment = pd.DataFrame({"Gender": ["Women", "Men"], "Rate": [unemployment.get("Women"), unemployment.get("Men")]})
    fig = px.bar(gender_unemployment, x="Gender", y="Rate", color="Gender", text_auto=".1f",
                 color_discrete_map=COLORS, title="Unemployment among each gender's labour force")
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, yaxis_title="Unemployment rate (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("3. Female unemployment by age")
    youth = age_unemployment[age_unemployment["Category"].isin(["15-19", "20-24"])].copy()
    female_age = pd.concat([
        pd.DataFrame({"Age group": ["All ages 15+"], "Rate": [unemployment.get("Women")]}),
        youth[["Category", "Women"]].rename(columns={"Category": "Age group", "Women": "Rate"}),
    ], ignore_index=True)
    fig = px.bar(female_age, x="Age group", y="Rate", text_auto=".1f", color_discrete_sequence=["#D96C5F"],
                 title="Women's unemployment: overall and selected youth age groups")
    fig.update_layout(**PLOT_LAYOUT, showlegend=False, yaxis_title="Unemployment rate (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("4. Labour-force participation by age")
    age_options = age_lfp["Category"].tolist()
    chosen_ages = st.multiselect("Select age groups", age_options, default=age_options, key="age_choice")
    age_view = age_lfp[age_lfp["Category"].isin(chosen_ages)]
    age_long = age_view.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Participation")
    fig = px.line(age_long, x="Category", y="Participation", color="Gender", markers=True,
                  color_discrete_map=COLORS, title="Participation rates across age groups")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Labour-force participation (%)", xaxis_title="Age group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("5. Labour-force participation by education")
    education_options = education_lfp["Category"].tolist()
    chosen_education = st.multiselect("Select education levels", education_options, default=education_options, key="education_choice")
    education_view = education_lfp[education_lfp["Category"].isin(chosen_education)]
    education_long = education_view.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Participation")
    fig = px.bar(education_long, x="Category", y="Participation", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Participation by completed education level")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Labour-force participation (%)", xaxis_title="", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("6. Education composition of employed women and men")
    employed_long = employed_education.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Share")
    fig = px.bar(employed_long, x="Category", y="Share", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Educational composition within each employed group")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Share of employed group (%)", xaxis_title="", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)
    st.caption("This chart describes the education composition of employed people; it is not a participation rate by education.")

    st.subheader("7. Employment status among employed people")
    status_long = employment_status.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Share")
    fig = px.bar(status_long, x="Category", y="Share", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Employment status within employed women and men")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Share within employed group (%)", xaxis_title="", xaxis_tickangle=-12)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("8. How unemployed people search for work")
    search_long = job_search.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Share")
    fig = px.bar(search_long, x="Category", y="Share", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Main job-search methods reported in the previous four weeks")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Share within unemployed group (%)", xaxis_title="", xaxis_tickangle=-12)
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View the tables used in the charts"):
        st.markdown("**Participation by age**")
        st.dataframe(age_lfp, use_container_width=True, hide_index=True)
        st.markdown("**Participation by education**")
        st.dataframe(education_lfp, use_container_width=True, hide_index=True)
        st.markdown("**Unemployment by education**")
        st.dataframe(education_unemployment, use_container_width=True, hide_index=True)
        st.download_button("Download participation by education (CSV)", education_lfp.to_csv(index=False).encode("utf-8-sig"), "participation_by_education_2022.csv", "text/csv")

with findings_tab:
    st.header("What does the evidence suggest?")
    st.write("The comparisons below highlight observed differences. They should not be interpreted as proof of the reasons behind those differences.")

    st.subheader("A. The education–participation relationship")
    edu_gap = education_lfp.copy()
    edu_gap["Gender gap"] = edu_gap["Men"] - edu_gap["Women"]
    edu_long = edu_gap.melt(id_vars=["Category", "Gender gap"], value_vars=["Women", "Men"], var_name="Gender", value_name="Participation")
    fig = px.bar(edu_long, x="Category", y="Participation", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Participation by completed education level and gender")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Labour-force participation (%)", xaxis_title="", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)
    university = education_lfp[education_lfp["Category"].str.lower().eq("university and above")]
    if not university.empty:
        uw = university.iloc[0]["Women"]
        um = university.iloc[0]["Men"]
        st.markdown(f'<div class="insight"><b>University education:</b> participation is {uw:.1f}% among women and {um:.1f}% among men, a difference of {um-uw:.1f} percentage points in the 2022 survey.</div>', unsafe_allow_html=True)

    st.subheader("B. How does the gender gap vary by age?")
    age_gap = age_lfp.copy()
    age_gap["Gap (men minus women)"] = age_gap["Men"] - age_gap["Women"]
    fig = px.bar(age_gap, x="Category", y="Gap (men minus women)", color="Gap (men minus women)",
                 color_continuous_scale=["#F2C7BF", "#D96C5F"], title="Participation gap by age group")
    fig.update_layout(**PLOT_LAYOUT, coloraxis_showscale=False, yaxis_title="Percentage-point gap", xaxis_title="Age group")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("C. Employment, unemployment and being outside the labour force")
    status_long = status_by_gender.melt(id_vars="Gender", value_vars=["Employed", "Unemployed", "Outside labour force"], var_name="Status", value_name="Share")
    fig = px.bar(status_long, x="Gender", y="Share", color="Status", barmode="stack",
                 color_discrete_map={"Employed": "#087E8B", "Unemployed": "#D7A84B", "Outside labour force": "#D96C5F"},
                 title="Distribution of residents aged 15+ by economic status")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Share of each gender (%)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("D. What types of employment do women and men hold?")
    fig = px.bar(status_long if False else employment_status.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Share"),
                 x="Category", y="Share", color="Gender", barmode="group", color_discrete_map=COLORS,
                 title="Employment status within employed women and men")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Share within employed group (%)", xaxis_title="", xaxis_tickangle=-12)
    st.plotly_chart(fig, use_container_width=True)
    employees = employment_status[employment_status["Category"].str.lower().eq("employees")]
    if not employees.empty:
        st.caption(f"Employees account for {employees.iloc[0]['Women']:.1f}% of employed women and {employees.iloc[0]['Men']:.1f}% of employed men in the survey table.")

    st.subheader("E. Unemployment by education")
    unemployment_long = education_unemployment.melt(id_vars="Category", value_vars=["Women", "Men"], var_name="Gender", value_name="Unemployment")
    fig = px.bar(unemployment_long, x="Category", y="Unemployment", color="Gender", barmode="group",
                 color_discrete_map=COLORS, title="Unemployment rates by completed education level")
    fig.update_layout(**PLOT_LAYOUT, yaxis_title="Unemployment rate (%)", xaxis_title="", xaxis_tickangle=-15)
    st.plotly_chart(fig, use_container_width=True)

    st.warning("The supplied tables do not provide the required cross-tabulations for marital status and household composition. These parts of the research question remain unanswered and would require additional survey microdata or official tables.")

with action_tab:
    st.header("From evidence to action")
    st.write("These are policy ideas suggested by the patterns in the data. They are proposals to evaluate, not impacts established by this descriptive analysis.")
    left, right = st.columns(2)
    with left:
        st.markdown("### 1 · Education-to-employment bridge\nStrengthen career guidance, internships, apprenticeships and employer partnerships so that educational qualifications connect more directly to paid work.")
        st.markdown("### 2 · Work and care support\nAssess access to affordable childcare, safe transport and flexible work arrangements, and evaluate whether these reduce barriers to employment.")
    with right:
        st.markdown("### 3 · Return-to-work pathways\nDevelop skills-refresh programmes, mentoring and structured re-entry opportunities for women returning to paid employment.")
        st.markdown("### 4 · Measure opportunity\nTrack recruitment, pay, promotion and employment conditions by gender and education to identify where gaps persist.")

with methods_tab:
    st.header("Methodology and sources")
    st.markdown("**National source:** Lebanon Labour Force and Household Living Conditions Survey 2022, tables EA1, EA3, EA6, EA8, EA37, EA39 and EA40.")
    st.markdown("**International source:** World Bank World Development Indicators modelled ILO unemployment estimates for Lebanon: total unemployment and male unemployment.")
    st.markdown("**Approach:** descriptive analysis of published cross-tabulations. Participation rates, unemployment rates, employment composition and employment status are kept distinct because they use different denominators.")
    st.markdown("**Limitations:** the national survey tables are for 2022; cross-sectional comparisons do not establish causality. The uploaded World Bank workbooks include total and male unemployment series, not a female series. Marital status and household composition are not available in the supplied cross-tabulations.")
    st.markdown("**Definitions:** labour-force participation is the share of the relevant population that is employed or unemployed; unemployment is measured among the labour force; people outside the labour force are neither employed nor unemployed under the survey's classification.")

st.markdown("---")
st.caption("The Invisible Workforce · Lebanon · Exploratory and explanatory data storytelling")
