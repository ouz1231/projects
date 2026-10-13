import os
from datetime import date

import pandas as pd
import streamlit as st


DIARY_FILE = "diary.csv"

st.title("📔 나의 일기장")

title = st.text_input("제목")
content = st.text_area("내용", height=150)
weather = st.selectbox("오늘의 날씨", ["맑음", "흐림", "비", "눈", "바람"])

if st.button("저장"):
    new_diary = pd.DataFrame(
        [
            {
                "날짜": date.today().isoformat(),
                "제목": title,
                "내용": content,
                "날씨": weather,
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

st.subheader("저장된 일기")
if os.path.exists(DIARY_FILE):
    diaries = pd.read_csv(DIARY_FILE, encoding="utf-8-sig")
    st.dataframe(diaries)
else:
    st.write("아직 작성된 일기가 없어요.")
