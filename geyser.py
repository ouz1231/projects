from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st


st.set_page_config(
    page_title="Old Faithful | Eruption patterns",
    page_icon="♨️",
    layout="wide",
    initial_sidebar_state="expanded",
)

LONG_COLOR = "#D85B45"
SHORT_COLOR = "#168A83"
PALETTE = {"long": LONG_COLOR, "short": SHORT_COLOR}
DATA_PATH = Path(__file__).parent / "data" / "geyser.csv"


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Gowun+Batang:wght@700&display=swap');
    :root {
        --ink: #202a2a;
        --muted: #687573;
        --line: #dce4e1;
        --paper: #f7f9f6;
        --accent: #168a83;
    }
    html, body, [class*="st-"] { font-family: 'DM Sans', 'Noto Sans KR', sans-serif; }
    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #edf3ef; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div { padding-top: 1.8rem; }
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
    [data-testid="stSidebarExpandButton"] [data-testid="stIconMaterial"] { font-size: 0 !important; }
    [data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"]::after { content: "‹"; font-size: 1.25rem; }
    [data-testid="stSidebarExpandButton"] [data-testid="stIconMaterial"]::after { content: "›"; font-size: 1.25rem; }
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {
        display: inline-block;
        width: .65rem;
        height: .65rem;
        font-size: 0 !important;
        line-height: 0;
    }
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"]::after {
        content: "";
        display: block;
        width: .45rem;
        height: .45rem;
        border-right: 2px solid currentColor;
        border-bottom: 2px solid currentColor;
        transform: rotate(45deg);
    }
    [data-testid="stExpander"] details[open] summary [data-testid="stIconMaterial"]::after {
        transform: rotate(225deg);
    }
    .block-container { max-width: 1500px; padding-top: 2.5rem; padding-bottom: 3rem; }
    .eyebrow { color: var(--accent); font-size: .72rem; font-weight: 700; text-transform: uppercase; }
    h1 { font-family: 'Gowun Batang', Georgia, serif !important; font-size: 2.3rem !important; color: var(--ink); }
    h2, h3 { color: var(--ink); }
    .lede { color: var(--muted); margin-top: -.45rem; margin-bottom: 1.4rem; }
    .metric-label { color: var(--muted); font-size: .78rem; font-weight: 600; }
    [data-testid="stMetric"] { border-top: 2px solid var(--line); padding: .85rem .1rem .35rem; }
    [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.8rem; }
    .section-kicker { color: var(--muted); font-size: .74rem; font-weight: 700; text-transform: uppercase; }
    div[data-testid="stPlotlyChart"], div[data-testid="stImage"] { border-radius: 4px; }
    .insight { border-left: 3px solid var(--accent); padding: .6rem .8rem; color: #43514e; background: #edf3ef; font-size: .88rem; }
    hr { border-color: var(--line); }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner="간헐천 관측 데이터를 불러오는 중...")
def load_data() -> tuple[pd.DataFrame, str]:
    """Load the seaborn dataset, falling back to the bundled CSV."""
    try:
        frame = sns.load_dataset("geyser")
        source = "Seaborn 데이터셋"
    except Exception as error:
        if not DATA_PATH.exists():
            raise FileNotFoundError(
                f"Seaborn 데이터셋 로드에 실패했고 백업 파일도 없습니다: {DATA_PATH}"
            ) from error
        frame = pd.read_csv(DATA_PATH)
        source = "로컬 CSV 백업"

    required = {"duration", "waiting", "kind"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"데이터에 필요한 컬럼이 없습니다: {', '.join(sorted(missing))}")

    frame = frame.loc[:, ["duration", "waiting", "kind"]].copy()
    frame["duration"] = pd.to_numeric(frame["duration"], errors="coerce")
    frame["waiting"] = pd.to_numeric(frame["waiting"], errors="coerce")
    frame = frame.dropna(subset=["duration", "waiting", "kind"])
    frame["kind"] = pd.Categorical(frame["kind"], categories=["long", "short"])
    frame["waiting_per_duration"] = frame["waiting"] / frame["duration"]
    return frame, source


def style_axis(axis: plt.Axes) -> None:
    axis.set_facecolor("#fbfcfa")
    axis.grid(axis="y", color="#e7ece9", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#cfd9d5")
    axis.tick_params(colors="#52615e", labelsize=9)
    axis.xaxis.label.set_color("#52615e")
    axis.yaxis.label.set_color("#52615e")


def finish_figure(figure: plt.Figure) -> None:
    figure.patch.set_facecolor("#f7f9f6")
    figure.tight_layout(pad=1.2)
    st.pyplot(figure, width="stretch")
    plt.close(figure)


def add_regression_line(axis: plt.Axes, frame: pd.DataFrame) -> None:
    if len(frame) < 2 or frame["duration"].nunique() < 2:
        return
    sns.regplot(
        data=frame,
        x="duration",
        y="waiting",
        scatter=False,
        ci=None,
        color="#263c39",
        line_kws={"linewidth": 2, "linestyle": "--", "alpha": 0.8},
        ax=axis,
    )


def scatter_plot(frame: pd.DataFrame, mode: str) -> None:
    if mode == "Plotly · hover":
        figure = px.scatter(
            frame,
            x="duration",
            y="waiting",
            color="kind",
            color_discrete_map=PALETTE,
            category_orders={"kind": ["long", "short"]},
            hover_data={"duration": ":.2f", "waiting": True, "kind": True},
            labels={"duration": "Duration (minutes)", "waiting": "Waiting (minutes)", "kind": "Eruption type"},
        )
        if len(frame) >= 2 and frame["duration"].nunique() >= 2:
            slope, intercept = np.polyfit(frame["duration"], frame["waiting"], 1)
            x_values = np.linspace(frame["duration"].min(), frame["duration"].max(), 50)
            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=slope * x_values + intercept,
                    mode="lines",
                    name="전체 추세",
                    line={"color": "#263c39", "dash": "dash", "width": 2},
                    hoverinfo="skip",
                )
            )
        figure.update_layout(
            height=390,
            margin={"l": 8, "r": 8, "t": 16, "b": 8},
            paper_bgcolor="#f7f9f6",
            plot_bgcolor="#fbfcfa",
            legend_title_text="분출 유형",
            font={"family": "DM Sans, Noto Sans KR, sans-serif", "color": "#52615e"},
        )
        figure.update_xaxes(showgrid=False, zeroline=False)
        figure.update_yaxes(gridcolor="#e7ece9", zeroline=False)
        st.plotly_chart(figure, use_container_width=True)
        return

    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    sns.scatterplot(
        data=frame,
        x="duration",
        y="waiting",
        hue="kind",
        style="kind",
        hue_order=["long", "short"],
        palette=PALETTE,
        alpha=0.78,
        s=55,
        ax=axis,
    )
    add_regression_line(axis, frame)
    axis.set(xlabel="Duration (minutes)", ylabel="Waiting (minutes)")
    axis.legend(title="Eruption type", frameon=False, fontsize=9)
    style_axis(axis)
    finish_figure(figure)


def density_plot(frame: pd.DataFrame) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    try:
        sns.kdeplot(
            data=frame,
            x="duration",
            y="waiting",
            fill=True,
            levels=10,
            thresh=0.04,
            cmap="mako",
            ax=axis,
        )
        sns.kdeplot(
            data=frame,
            x="duration",
            y="waiting",
            levels=5,
            color="#f7f9f6",
            linewidths=0.8,
            ax=axis,
        )
    except (ValueError, np.linalg.LinAlgError):
        axis.clear()
        axis.hexbin(
            frame["duration"],
            frame["waiting"],
            gridsize=18,
            mincnt=1,
            cmap="mako",
            linewidths=0,
        )
        axis.text(
            0.02,
            0.98,
            "Hex bins shown because the filtered sample is sparse",
            transform=axis.transAxes,
            va="top",
            color="#52615e",
            fontsize=8,
        )
    axis.set(xlabel="Duration (minutes)", ylabel="Waiting (minutes)")
    style_axis(axis)
    finish_figure(figure)


def distribution_plots(frame: pd.DataFrame) -> None:
    waiting_figure, waiting_axis = plt.subplots(figsize=(7.2, 3.7))
    sns.histplot(
        data=frame,
        x="waiting",
        hue="kind",
        hue_order=["long", "short"],
        palette=PALETTE,
        stat="density",
        common_norm=False,
        element="step",
        fill=True,
        alpha=0.2,
        kde=True,
        ax=waiting_axis,
    )
    sns.rugplot(data=frame, x="waiting", color="#44534f", alpha=0.16, height=0.035, ax=waiting_axis)
    for peak, color in [(55, SHORT_COLOR), (80, LONG_COLOR)]:
        waiting_axis.axvline(peak, color=color, linestyle="--", linewidth=1.4, alpha=0.85)
    waiting_axis.set(xlabel="Waiting (minutes)", ylabel="Density")
    style_axis(waiting_axis)
    finish_figure(waiting_figure)

    duration_figure, duration_axis = plt.subplots(figsize=(7.2, 3.7))
    sns.histplot(
        data=frame,
        x="duration",
        hue="kind",
        hue_order=["long", "short"],
        palette=PALETTE,
        stat="density",
        common_norm=False,
        element="step",
        fill=True,
        alpha=0.2,
        kde=True,
        ax=duration_axis,
    )
    for center, color in [(2, SHORT_COLOR), (4.5, LONG_COLOR)]:
        duration_axis.axvline(center, color=color, linestyle="--", linewidth=1.4, alpha=0.85)
    duration_axis.set(xlabel="Duration (minutes)", ylabel="Density")
    style_axis(duration_axis)
    finish_figure(duration_figure)


def comparison_plots(frame: pd.DataFrame, metric: str, label: str) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    sns.violinplot(
        data=frame,
        x="kind",
        y=metric,
        hue="kind",
        order=["long", "short"],
        hue_order=["long", "short"],
        palette=PALETTE,
        inner="quart",
        cut=0,
        legend=False,
        ax=axis,
    )
    sns.stripplot(
        data=frame,
        x="kind",
        y=metric,
        hue="kind",
        order=["long", "short"],
        hue_order=["long", "short"],
        palette=PALETTE,
        dodge=False,
        alpha=0.28,
        size=3,
        legend=False,
        ax=axis,
    )
    sns.boxplot(
        data=frame,
        x="kind",
        y=metric,
        hue="kind",
        order=["long", "short"],
        hue_order=["long", "short"],
        palette=PALETTE,
        width=0.14,
        showfliers=False,
        boxprops={"facecolor": "none", "edgecolor": "#263c39", "zorder": 3},
        medianprops={"color": "#263c39", "linewidth": 1.5},
        whiskerprops={"color": "#263c39"},
        capprops={"color": "#263c39"},
        legend=False,
        ax=axis,
    )
    axis.set(xlabel="Eruption type", ylabel=label)
    style_axis(axis)
    finish_figure(figure)


def mean_plot(frame: pd.DataFrame, metric: str, label: str) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    sns.barplot(
        data=frame,
        x="kind",
        y=metric,
        hue="kind",
        order=["long", "short"],
        hue_order=["long", "short"],
        palette=PALETTE,
        estimator="mean",
        errorbar="sd",
        capsize=0.12,
        legend=False,
        ax=axis,
    )
    axis.set(xlabel="Eruption type", ylabel=f"Mean {label} (standard deviation)")
    style_axis(axis)
    finish_figure(figure)


data, data_source = load_data()
duration_bounds = (float(data["duration"].min()), float(data["duration"].max()))
waiting_bounds = (int(data["waiting"].min()), int(data["waiting"].max()))

with st.sidebar:
    st.markdown("<div class='eyebrow'>관측 데이터 탐색</div>", unsafe_allow_html=True)
    st.header("필터")
    selected_kinds = st.multiselect(
        "분출 유형",
        options=["long", "short"],
        default=["long", "short"],
        format_func=lambda kind: "긴 분출 · Long" if kind == "long" else "짧은 분출 · Short",
    )
    selected_duration = st.slider(
        "분출시간 (분)",
        min_value=duration_bounds[0],
        max_value=duration_bounds[1],
        value=duration_bounds,
        step=0.1,
        format="%.1f",
    )
    selected_waiting = st.slider(
        "대기시간 (분)",
        min_value=waiting_bounds[0],
        max_value=waiting_bounds[1],
        value=waiting_bounds,
        step=1,
    )
    chart_mode = st.radio(
        "산점도 모드",
        ["Seaborn", "Plotly · hover"],
        horizontal=True,
    )
    st.divider()
    st.caption(f"데이터 출처 · {data_source}")
    st.caption("Old Faithful 간헐천 · 272회 관측")

filtered = data.loc[
    data["kind"].isin(selected_kinds)
    & data["duration"].between(*selected_duration)
    & data["waiting"].between(*selected_waiting)
].copy()

st.markdown("<div class='eyebrow'>YELLOWSTONE · OLD FAITHFUL</div>", unsafe_allow_html=True)
st.title("분출이 길면, 다음 대기도 길어질까?")
st.markdown(
    "<p class='lede'>간헐천 272회 관측에서 분출시간과 다음 분출까지의 대기 패턴을 읽습니다.</p>",
    unsafe_allow_html=True,
)

if data_source == "로컬 CSV 백업":
    st.info("Seaborn 원격 데이터에 연결하지 못해 프로젝트에 포함된 CSV 백업을 사용하고 있습니다.")

long_share = filtered["kind"].eq("long").mean() * 100 if not filtered.empty else 0
short_share = filtered["kind"].eq("short").mean() * 100 if not filtered.empty else 0
metrics = st.columns(4)
metrics[0].metric("관측 수", f"{len(filtered):,}회", f"전체 {len(data):,}회 중")
metrics[1].metric("Long / Short", f"{long_share:.1f}% / {short_share:.1f}%", "필터 내 분출 비율")
metrics[2].metric("평균 대기시간", f"{filtered['waiting'].mean():.1f}분" if not filtered.empty else "—")
metrics[3].metric("평균 분출시간", f"{filtered['duration'].mean():.2f}분" if not filtered.empty else "—")

st.divider()

if filtered.empty:
    st.warning("조건에 맞는 관측이 없습니다. 사이드바 필터를 넓혀 주세요.")
else:
    st.markdown("<div class='section-kicker'>01 · 관계와 밀도</div>", unsafe_allow_html=True)
    scatter_column, density_column = st.columns(2, gap="large")
    with scatter_column:
        st.subheader("분출시간과 대기시간")
        st.caption("분출이 길었던 관측일수록 다음 대기시간도 길어지는 경향")
        scatter_plot(filtered, chart_mode)
    with density_column:
        st.subheader("관측이 몰리는 구간")
        st.caption("색이 밝을수록 해당 조합에 관측이 밀집")
        density_plot(filtered)

    if len(filtered) > 1 and filtered["duration"].nunique() > 1:
        correlation = filtered["duration"].corr(filtered["waiting"])
        st.markdown(
            f"<div class='insight'>분출시간과 대기시간의 상관계수는 <b>{correlation:.2f}</b>입니다. "
            "두 변수의 관계는 뚜렷하지만, 상관관계만으로 개별 대기시간을 확정할 수는 없습니다.</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("<div class='section-kicker'>02 · 분포의 두 봉우리</div>", unsafe_allow_html=True)
    waiting_column, duration_column = st.columns(2, gap="large")
    with waiting_column:
        st.subheader("대기시간")
        st.caption("약 55분과 80분 부근에 짧은 대기·긴 대기 그룹이 나타납니다.")
    with duration_column:
        st.subheader("분출시간")
        st.caption("약 2분의 짧은 분출과 4.5분 안팎의 긴 분출로 나뉩니다.")
    distribution_plots(filtered)

    st.divider()
    st.markdown("<div class='section-kicker'>03 · 유형별 비교</div>", unsafe_allow_html=True)
    comparison_column, average_column = st.columns(2, gap="large")
    with comparison_column:
        st.subheader("그룹 안의 분포")
        comparison_metric = st.tabs(["대기시간", "분출시간"])
        with comparison_metric[0]:
            comparison_plots(filtered, "waiting", "대기시간 (분)")
        with comparison_metric[1]:
            comparison_plots(filtered, "duration", "분출시간 (분)")
    with average_column:
        st.subheader("유형별 평균과 변동")
        average_metric = st.tabs(["대기시간", "분출시간"])
        with average_metric[0]:
            mean_plot(filtered, "waiting", "대기시간")
        with average_metric[1]:
            mean_plot(filtered, "duration", "분출시간")

    summary = (
        filtered.groupby("kind", observed=False)
        .agg(
            관측수=("duration", "count"),
            평균_분출시간=("duration", "mean"),
            표준편차_분출시간=("duration", "std"),
            평균_대기시간=("waiting", "mean"),
            표준편차_대기시간=("waiting", "std"),
            평균_대기효율=("waiting_per_duration", "mean"),
        )
        .rename_axis("분출 유형")
    )
    st.dataframe(summary.style.format("{:.2f}", subset=summary.columns[1:]), width="stretch")

with st.expander("필터된 관측 데이터 보기"):
    st.dataframe(filtered, width="stretch", hide_index=True)

st.download_button(
    "필터된 CSV 다운로드",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="geyser_filtered.csv",
    mime="text/csv",
    disabled=filtered.empty,
)
st.caption("출처: Seaborn geyser 데이터셋 · eruptions (분), waiting (분), kind (분출 유형)")