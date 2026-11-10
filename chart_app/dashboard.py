import calendar

import plotly.express as px
import seaborn as sns
import streamlit as st


st.set_page_config(page_title="📊 데이터 분석 대시보드", layout="wide")


def render_flights_tab() -> None:
    flights = sns.load_dataset("flights")
    month_numbers = {
        **{calendar.month_name[number]: number for number in range(1, 13)},
        **{calendar.month_abbr[number]: number for number in range(1, 13)},
    }
    flights["month_number"] = flights["month"].map(month_numbers).astype(int)
    flights["month_label"] = flights["month_number"].map(
        lambda month: f"{month}월"
    )

    st.title("✈️ 항공 승객 분석")

    total_rows, year_metrics, passenger_metrics = st.columns(3)
    with total_rows:
        st.metric("총 행 수", f"{len(flights):,}행")
    with year_metrics:
        st.metric("연도 범위", f"{flights['year'].min()}–{flights['year'].max()}년")
    with passenger_metrics:
        st.metric("최대 승객 수", f"{flights['passengers'].max():,}명")

    month_range = st.sidebar.slider(
        "월 범위",
        min_value=1,
        max_value=12,
        value=(1, 12),
        format="%d월",
    )

    selected_flights = flights[
        flights["month_number"].between(month_range[0], month_range[1])
    ]
    yearly_average = (
        selected_flights.groupby("year", as_index=False)["passengers"]
        .mean()
        .sort_values("year")
    )
    yearly_average["rolling_mean"] = yearly_average["passengers"].rolling(window=3).mean()
    yearly_lines = yearly_average.melt(
        id_vars="year",
        value_vars=["passengers", "rolling_mean"],
        var_name="series",
        value_name="average_passengers",
    )
    yearly_lines["series"] = yearly_lines["series"].map(
        {"passengers": "연도별 평균", "rolling_mean": "3년 이동평균"}
    )

    st.subheader("연도별 평균 승객 수 및 3년 이동평균")
    fig = px.line(
        yearly_lines,
        x="year",
        y="average_passengers",
        color="series",
        labels={
            "year": "연도",
            "average_passengers": "평균 승객 수",
            "series": "구분",
        },
        color_discrete_map={"연도별 평균": "#1f77b4", "3년 이동평균": "#ff7f0e"},
    )
    fig.update_traces(selector={"name": "3년 이동평균"}, line={"dash": "dash"})
    st.plotly_chart(fig, use_container_width=True)

    monthly_average = (
        flights.groupby(["month_number", "month_label"], as_index=False)["passengers"]
        .mean()
        .sort_values("month_number")
    )
    month_order = [f"{month}월" for month in range(1, 13)]

    st.subheader("월별 평균 승객 수")
    fig = px.bar(
        monthly_average,
        x="month_label",
        y="passengers",
        category_orders={"month_label": month_order},
        labels={"month_label": "월", "passengers": "평균 승객 수"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("월별 승객 수 분포")
    fig = px.box(
        flights,
        x="month_label",
        y="passengers",
        category_orders={"month_label": month_order},
        labels={"month_label": "월", "passengers": "승객 수"},
    )
    st.plotly_chart(fig, use_container_width=True)

    passenger_pivot = flights.pivot_table(
        index="year",
        columns="month_number",
        values="passengers",
        aggfunc="mean",
    ).reindex(columns=range(1, 13))

    st.subheader("연도별·월별 승객 수 히트맵")
    fig = px.imshow(
        passenger_pivot,
        x=month_order,
        y=passenger_pivot.index,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".0f",
        labels={"x": "월", "y": "연도", "color": "승객 수"},
    )
    fig.update_traces(textfont={"size": 12, "color": "#111827"})
    st.plotly_chart(fig, use_container_width=True)


def render_tips_tab() -> None:
    tips = sns.load_dataset("tips")
    column_options = {
        "성별(sex)": "sex",
        "흡연여부(smoker)": "smoker",
        "요일(day)": "day",
        "시간대(time)": "time",
    }

    st.title("🍽️ 레스토랑 팁 분석")

    st.subheader("기술 통계 요약")
    (
        total_bill_metric,
        average_bill_metric,
        average_tip_metric,
        average_tip_rate_metric,
    ) = st.columns(4)
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


flights_tab, tips_tab = st.tabs(["✈️ 항공 승객 분석", "🍽️ 레스토랑 팁 분석"])

with flights_tab:
    render_flights_tab()

with tips_tab:
    render_tips_tab()
