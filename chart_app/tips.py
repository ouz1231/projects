import plotly.express as px
import seaborn as sns
import streamlit as st


st.set_page_config(page_title="🍽️ 레스토랑 팁 분석", layout="wide")

tips = sns.load_dataset("tips")
column_options = {
    "성별(sex)": "sex",
    "흡연여부(smoker)": "smoker",
    "요일(day)": "day",
    "시간대(time)": "time",
}

st.title("🍽️ 레스토랑 팁 분석")

st.subheader("기술 통계 요약")
total_bill_metric, average_bill_metric, average_tip_metric, average_tip_rate_metric = (
    st.columns(4)
)
with total_bill_metric:
    st.metric("총 데이터 수", f"{len(tips):,}건")
with average_bill_metric:
    st.metric("평균 식사 금액", f"${tips['total_bill'].mean():.2f}")
with average_tip_metric:
    st.metric("평균 팁 금액", f"${tips['tip'].mean():.2f}")
with average_tip_rate_metric:
    average_tip_rate = (tips["tip"] / tips["total_bill"]).mean() * 100
    st.metric("평균 팁 비율", f"{average_tip_rate:.2f}%")

st.dataframe(tips.describe(), use_container_width=True)

st.subheader("식사 금액과 팁 금액의 관계")
scatter_color_label = st.sidebar.selectbox(
    "산점도 색상 기준",
    list(column_options),
)
scatter_color_column = column_options[scatter_color_label]
fig = px.scatter(
    tips,
    x="total_bill",
    y="tip",
    color=scatter_color_column,
    trendline="ols",
    hover_data={
        "total_bill": ":.2f",
        "tip": ":.2f",
        "size": True,
    },
    labels={
        "total_bill": "식사 금액 ($)",
        "tip": "팁 금액 ($)",
        "size": "인원수",
        scatter_color_column: scatter_color_label,
    },
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("조건별 총 식사 금액 합계")
bar_group_label = st.sidebar.selectbox(
    "막대차트 그룹 기준",
    list(column_options),
)
bar_group_column = column_options[bar_group_label]
grouped_bills = (
    tips.groupby(bar_group_column, as_index=False, observed=True)["total_bill"]
    .sum()
    .sort_values(bar_group_column)
)
fig = px.bar(
    grouped_bills,
    x=bar_group_column,
    y="total_bill",
    text="total_bill",
    title="선택 기준별 총 식사 금액 합계",
    labels={
        bar_group_column: bar_group_label,
        "total_bill": "총 식사 금액 ($)",
    },
)
fig.update_traces(
    texttemplate="$%{y:,.2f}",
    textposition="outside",
    cliponaxis=False,
)
st.plotly_chart(fig, use_container_width=True)
