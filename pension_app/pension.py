from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


APP_DIR = Path(__file__).resolve().parent
DATA_PATH = APP_DIR / "data" / "cleaned_pension.csv"
PENSION_RATE = 0.095
SALARY_CAP = 6_590_000


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


st.set_page_config(page_title="📋 국민연금 사업장 분석 대시보드", layout="wide")
st.title("📋 국민연금 사업장 분석 대시보드")

try:
    df = load_data(DATA_PATH)
except (FileNotFoundError, OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
    st.error(f"전처리된 CSV 파일을 읽지 못했습니다: {error}")
    st.stop()

required_columns = {
    "member_count",
    "charge_amount",
    "company_type",
    "sido",
    "industry",
    "estimated_salary_per",
}
missing_columns = sorted(required_columns.difference(df.columns))
if missing_columns:
    st.error(f"CSV에 필요한 컬럼이 없습니다: {', '.join(missing_columns)}")
    st.stop()
if df.empty:
    st.error("분석할 데이터가 없습니다.")
    st.stop()

with st.sidebar:
    st.header("지역 선택")
    sido_options = sorted(df["sido"].dropna().astype(str).unique())
    selected_sido = st.selectbox("시도", options=sido_options)

    st.header("분석 필터")
    selected_company_type = st.selectbox("사업장 형태", options=["전체", "법인", "개인"])
    minimum_members = st.slider("최소 가입자 수", min_value=1, max_value=100, value=1)

member_counts = pd.to_numeric(df["member_count"], errors="coerce").fillna(0)
charge_amounts = pd.to_numeric(df["charge_amount"], errors="coerce").fillna(0)
estimated_salaries = pd.to_numeric(df["estimated_salary_per"], errors="coerce")
df = df.assign(
    member_count=member_counts,
    charge_amount=charge_amounts,
    estimated_salary_per=estimated_salaries,
)
total_members = member_counts.sum()
estimated_average_salary = (
    min(charge_amounts.sum() / PENSION_RATE / total_members, SALARY_CAP)
    if total_members > 0
    else 0
)

if "year_month" in df.columns:
    year_month_values = df["year_month"].dropna().astype(str)
    latest_year_month = year_month_values.max() if not year_month_values.empty else "확인 불가"
else:
    latest_year_month = "확인 불가"
    st.warning("CSV에 year_month 컬럼이 없어 데이터 기준 연월을 표시할 수 없습니다.")

company_metric, member_metric, salary_metric, date_metric = st.columns(4)
company_metric.metric("총 등록 사업장 수", f"{len(df):,}")
member_metric.metric("총 가입자 수", f"{total_members:,.0f}")
salary_metric.metric("전국 평균 1인당 추정 월급여", f"{estimated_average_salary:,.0f}원")
date_metric.metric("데이터 기준 연월", latest_year_month)

filtered_df = df.loc[
    (df["sido"].astype("string") == selected_sido)
    & (df["member_count"] >= minimum_members)
]
if selected_company_type != "전체":
    filtered_df = filtered_df.loc[filtered_df["company_type"] == selected_company_type]

filtered_member_total = filtered_df["member_count"].sum()
filtered_charge_total = filtered_df["charge_amount"].sum()
filtered_average_salary = (
    min(filtered_charge_total / PENSION_RATE / filtered_member_total, SALARY_CAP)
    if filtered_member_total > 0
    else 0
)

st.subheader(f"{selected_sido} 분석 결과")
st.caption(
    f"사업장 형태: {selected_company_type} · "
    f"최소 가입자 수: {minimum_members:,}명 이상"
)

regional_average_salary = filtered_average_salary
salary_difference = regional_average_salary - estimated_average_salary

regional_company_metric, regional_member_metric, regional_salary_metric, salary_delta_metric = (
    st.columns(4)
)
regional_company_metric.metric("해당 시도 사업장 수", f"{len(filtered_df):,}")
regional_member_metric.metric("해당 시도 총 가입자 수", f"{filtered_member_total:,.0f}")
regional_salary_metric.metric("해당 시도 평균 1인당 추정 월급여", f"{regional_average_salary:,.0f}원")
salary_delta_metric.metric(
    "전국 평균 대비 차이",
    f"{salary_difference:+,.0f}원",
    delta=f"{salary_difference:+,.0f}원",
    delta_color="normal",
)

chart_df = filtered_df.assign(
    industry=filtered_df["industry"].fillna("업종 정보 없음"),
    estimated_salary_per=pd.to_numeric(filtered_df["estimated_salary_per"], errors="coerce"),
)

st.subheader("업종별 사업장 수 TOP 10")
industry_company_counts = (
    chart_df.groupby("industry")
    .size()
    .nlargest(10)
    .sort_values(ascending=True)
    .rename("사업장 수")
    .reset_index()
)
company_count_fig = px.bar(
    industry_company_counts,
    x="사업장 수",
    y="industry",
    orientation="h",
    title="선택 시도 업종별 사업장 수 TOP 10",
)
company_count_fig.update_layout(yaxis_title="업종", xaxis_title="사업장 수")
st.plotly_chart(company_count_fig, use_container_width=True)

st.subheader("업종별 평균 1인당 추정 월급여 TOP 10")
industry_salary_means = (
    chart_df.dropna(subset=["estimated_salary_per"])
    .groupby("industry")["estimated_salary_per"]
    .mean()
    .nlargest(10)
    .sort_values(ascending=True)
    .rename("평균 추정 월급여")
    .reset_index()
)
industry_salary_means["금액"] = industry_salary_means["평균 추정 월급여"].map(
    lambda amount: f"{amount:,.0f}원"
)
salary_fig = px.bar(
    industry_salary_means,
    x="평균 추정 월급여",
    y="industry",
    text="금액",
    orientation="h",
    title="선택 시도 업종별 평균 추정 월급여 TOP 10",
)
salary_fig.update_traces(textposition="outside", cliponaxis=False)
salary_fig.add_vline(
    x=SALARY_CAP,
    line_dash="dash",
    line_color="red",
    annotation_text="기준소득 상한액",
)
salary_fig.update_layout(yaxis_title="업종", xaxis_title="평균 추정 월급여 (원)")
st.plotly_chart(salary_fig, use_container_width=True)

st.subheader("사업장 목록")
st.dataframe(
    filtered_df[
        ["company_name", "industry", "sido", "company_type", "member_count", "charge_amount"]
    ].head(1_000),
    width="stretch",
    hide_index=True,
)
if len(filtered_df) > 1_000:
    st.caption(f"전체 {len(filtered_df):,}개 사업장 중 상위 1,000개를 표시합니다.")
