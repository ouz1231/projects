import calendar
import json
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

DIARY_FILE = "diary.csv"
SETTINGS_FILE = "settings.json"
THEME_OPTIONS = ["파랑", "초록", "보라", "주황", "빨강"]

# 톤온톤 배색 정의 (메인 화이트 기반 + 테마별 배경, 사이드바, 포인트 컬러)
THEME_PALETTES = {
    "파랑": {
        "primary": "#2563eb",
        "hover": "#1d4ed8",
        "light_bg": "#eff6ff",
        "border": "#bfdbfe",
        "sidebar_bg": "#f8fafc",
        "main_bg": "#ffffff",
    },
    "초록": {
        "primary": "#16a34a",
        "hover": "#15803d",
        "light_bg": "#f0fdf4",
        "border": "#bbf7d0",
        "sidebar_bg": "#f8fafc",
        "main_bg": "#ffffff",
    },
    "보라": {
        "primary": "#7c3aed",
        "hover": "#6d28d9",
        "light_bg": "#f5f3ff",
        "border": "#e9d5ff",
        "sidebar_bg": "#f8fafc",
        "main_bg": "#ffffff",
    },
    "주황": {
        "primary": "#ea580c",
        "hover": "#c2410c",
        "light_bg": "#fff7ed",
        "border": "#fed7aa",
        "sidebar_bg": "#f8fafc",
        "main_bg": "#ffffff",
    },
    "빨강": {
        "primary": "#dc2626",
        "hover": "#b91c1c",
        "light_bg": "#fef2f2",
        "border": "#fecaca",
        "sidebar_bg": "#f8fafc",
        "main_bg": "#ffffff",
    },
}


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as settings_file:
                settings = json.load(settings_file)
        except (OSError, json.JSONDecodeError):
            settings = {}
    else:
        settings = {}

    if not isinstance(settings, dict):
        settings = {}

    theme = settings.get("theme", "파랑")
    if theme not in THEME_OPTIONS:
        theme = "파랑"

    return {
        "author_name": settings.get("author_name", ""),
        "theme": theme,
        "last_viewed_date": settings.get("last_viewed_date"),
    }


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, ensure_ascii=False, indent=2)


settings = load_settings()
is_first_visit = not settings["last_viewed_date"]
settings["last_viewed_date"] = date.today().isoformat()
save_settings(settings)

current_theme = settings["theme"]
palette = THEME_PALETTES[current_theme]

# 동적 CSS 주입 (메인 배경, 사이드바 배경, 버튼, 포커스 색상 일괄 적용)
st.markdown(
    f"""
    <style>
        /* 전체 메인 앱 배경 */
        .stApp {{
            background-color: {palette['main_bg']};
        }}
        /* 사이드바 배경 및 테두리 */
        [data-testid="stSidebar"] {{
            background-color: {palette['light_bg']};
            border-right: 1px solid {palette['border']};
        }}
        /* 메인 버튼 스타일 */
        .stButton>button {{
            background-color: {palette['primary']};
            color: white;
            border-radius: 6px;
            border: none;
            font-weight: 600;
            width: 100%;
        }}
        .stButton>button:hover {{
            background-color: {palette['hover']};
            color: white;
        }}
        /* 입력창 포커스 효과 */
        .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
            border-color: {palette['primary']};
            box-shadow: 0 0 0 1px {palette['primary']};
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.subheader("설정")
author_name = st.sidebar.text_input("작성자 이름", value=settings["author_name"])
if st.sidebar.button("이름 저장"):
    settings["author_name"] = author_name
    save_settings(settings)
    st.sidebar.success("이름이 저장되었습니다.")

theme = st.sidebar.selectbox(
    "테마 색상",
    THEME_OPTIONS,
    index=THEME_OPTIONS.index(current_theme),
)
if theme != current_theme:
    settings["theme"] = theme
    save_settings(settings)
    st.rerun()

# 상단 테마 안내 배너
st.markdown(
    f'<div style="background-color: {palette["light_bg"]}; border: 1px solid {palette["border"]}; '
    f'padding: 12px; border-radius: 6px; color: {palette["primary"]}; font-weight: bold; text-align: center;">'
    f'현재 적용된 테마: {current_theme}'
    f'</div>',
    unsafe_allow_html=True,
)

st.title("📔 나의 일기장")

# 일기 작성 폼
title = st.text_input("제목")
content = st.text_area("내용", height=150)

col1, col2 = st.columns(2)
with col1:
    weather = st.selectbox("오늘의 날씨", ["맑음", "흐림", "비", "눈", "바람"])
with col2:
    mood = st.selectbox(
        "오늘의 기분",
        ["행복함 😊", "신남 🥳", "평온함 😐", "슬픔 😢", "피곤함 😴", "지침 😩"],
    )

food = st.text_input("오늘 먹은 음식 (선택)")

if st.button("일기 저장"):
    new_diary = pd.DataFrame(
        [
            {
                "날짜": date.today().isoformat(),
                "작성자": author_name,
                "제목": title,
                "내용": content,
                "날씨": weather,
                "기분": mood,
                "먹은음식": food,
            }
        ]
    )

    if os.path.exists(DIARY_FILE):
        diaries = pd.read_csv(DIARY_FILE, encoding="utf-8-sig")
        diaries = pd.concat([diaries, new_diary], ignore_index=True)
    else:
        diaries = new_diary

    diaries.to_csv(DIARY_FILE, index=False, encoding="utf-8-sig")
    st.success("일기가 저장되었습니다.")

st.divider()

# 캘린더 뷰 (일별 기록 건수 표시)
st.subheader("📅 월별 일기 캘린더")
if os.path.exists(DIARY_FILE):
    diaries = pd.read_csv(DIARY_FILE, encoding="utf-8-sig")
    if not diaries.empty:
        diaries["날짜_str"] = pd.to_datetime(diaries["날짜"]).dt.strftime(
            "%Y-%m-%d"
        )
        date_counts = diaries["날짜_str"].value_counts().to_dict()

        now = datetime.now()
        c1, c2 = st.columns(2)
        with c1:
            selected_year = st.selectbox(
                "연도 선택", range(now.year - 2, now.year + 2), index=2
            )
        with c2:
            selected_month = st.selectbox(
                "월 선택", range(1, 13), index=now.month - 1
            )

        cal = calendar.monthcalendar(selected_year, selected_month)
        week_days = ["월", "화", "수", "목", "금", "토", "일"]

        cols = st.columns(7)
        for i, day_name in enumerate(week_days):
            cols[i].markdown(
                f"<div style='text-align: center; font-weight: bold; color: #4b5563;'>{day_name}</div>",
                unsafe_allow_html=True,
            )

        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day == 0:
                    cols[i].markdown(
                        "<div style='text-align: center; color: #e5e7eb;'>-</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    date_str = (
                        f"{selected_year}-{selected_month:02d}-{day:02d}"
                    )
                    count = date_counts.get(date_str, 0)
                    if count > 0:
                        cols[i].markdown(
                            f"<div style='text-align: center; background-color: {palette['light_bg']}; "
                            f"border: 1px solid {palette['border']}; border-radius: 6px; padding: 6px;'>"
                            f"<b style='color: #1f2937;'>{day}</b><br>"
                            f"<span style='font-size: 11px; color: {palette['primary']}; font-weight: 600;'>📝 {count}건</span></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        cols[i].markdown(
                            f"<div style='text-align: center; padding: 6px; color: #374151;'>{day}</div>",
                            unsafe_allow_html=True,
                        )
    else:
        st.write("작성된 일기가 없어 캘린더를 표시할 수 없음.")
else:
    st.write("작성된 일기가 없음.")

st.divider()

# 저장된 일기 조회 및 삭제 기능
st.subheader("📚 저장된 일기 관리 및 삭제")
if os.path.exists(DIARY_FILE):
    diaries = pd.read_csv(DIARY_FILE, encoding="utf-8-sig")
    if not diaries.empty:
        diary_options = [
            f"[{row['날짜']}] {row['제목']} (기분: {row['기분']})"
            for idx, row in diaries.iterrows()
        ]
        selected_to_delete = st.selectbox(
            "삭제할 일기 선택", options=["선택하세요"] + diary_options
        )

        if selected_to_delete != "선택하세요":
            if st.button("선택한 일기 영구 삭제"):
                selected_idx = diary_options.index(selected_to_delete)
                diaries = diaries.drop(selected_idx).reset_index(drop=True)
                diaries.to_csv(DIARY_FILE, index=False, encoding="utf-8-sig")
                st.success("선택한 일기가 삭제되었습니다.")
                st.rerun()

        st.dataframe(diaries, use_container_width=True)
    else:
        st.write("아직 작성된 일기가 없어요.")
else:
    st.write("아직 작성된 일기가 없어요.")

if is_first_visit:
    st.caption("처음 방문이에요! 일기를 써봐요 🌱")
else:
    st.caption(f"마지막으로 일기를 확인한 날: {settings['last_viewed_date']}")
    