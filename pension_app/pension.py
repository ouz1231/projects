import os

import pandas as pd
import streamlit as st


APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
INPUT_PATH = os.path.join(DATA_DIR, "pension_raw.csv")
OUTPUT_PATH = os.path.join(DATA_DIR, "cleaned_pension.csv")


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding="cp949")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="utf-8-sig")


def show_step(title: str, message: str, frame: pd.DataFrame) -> None:
    with st.expander(title, expanded=True):
        st.success(message)
        st.dataframe(frame.head(), width="stretch")


st.set_page_config(page_title="국민연금 사업장 데이터 전처리", layout="wide")
st.title("📋 국민연금 사업장 데이터 전처리")

try:
    raw_df = load_data(INPUT_PATH)
except (FileNotFoundError, OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
    st.error(f"CSV 파일을 읽지 못했습니다: {error}")
    st.stop()

source_row_count = len(raw_df)

st.subheader("전처리 전·후 행 수")
before_metric, after_metric = st.columns(2)

step1_df = raw_df.copy()
show_step("1단계. CSV 읽기", f"원본 CSV를 읽었습니다. 전체 {len(step1_df):,}행입니다.", step1_df)

source_columns = {
    "사업장명": "company_name",
    "사업장가입상태코드 1 등록 2 탈퇴": "status_code",
    "사업장도로명상세주소": "address",
    "법정동주소광역시도코드": "sido_code",
    "사업장업종코드명": "industry",
    "가입자수": "member_count",
    "당월고지금액": "charge_amount",
    "사업장형태구분코드 1 법인 2 개인": "type_code",
    "신규취득자수": "new_members",
    "상실가입자수": "lost_members",
}
missing_columns = [column for column in source_columns if column not in raw_df.columns]
if missing_columns:
    st.error(f"원본 CSV에 필요한 컬럼이 없습니다: {', '.join(missing_columns)}")
    st.stop()

step2_df = raw_df[list(source_columns)].copy()
show_step(
    "2단계. 필요한 컬럼 선택",
    "전처리에 필요한 컬럼을 선택했습니다. 이후 단계에 필요한 법인/개인 구분과 신규·상실 가입자 컬럼도 포함했습니다.",
    step2_df,
)

step3_df = step2_df.rename(columns=source_columns)
show_step("3단계. 컬럼명 영문으로 변경", "필요한 컬럼명을 영문으로 변경했습니다.", step3_df)

step4_df = step3_df.copy()
step4_df["status"] = (
    step4_df["status_code"].astype("string").str.strip().map({"1": "등록", "2": "탈퇴"})
)
step4_df["company_type"] = (
    step4_df["type_code"].astype("string").str.strip().map({"1": "법인", "2": "개인"})
)
step4_df = step4_df.drop(columns=["status_code", "type_code"])
show_step(
    "4단계. 코드값을 텍스트로 변환",
    "가입 상태와 사업장 형태 코드를 텍스트로 바꾸고 원본 코드 컬럼을 제거했습니다.",
    step4_df,
)

step5_df = step4_df.copy()
step5_df["sido"] = step5_df["address"].astype("string").str.strip().str.split().str[0]
step5_df = step5_df.drop(columns=["address", "sido_code"])
show_step("5단계. 시도명 추출", "도로명 주소의 첫 단어를 시도명으로 추출했습니다.", step5_df)

step6_df = step5_df.copy()
numeric_columns = ["member_count", "charge_amount", "new_members", "lost_members"]
for column in numeric_columns:
    step6_df[column] = pd.to_numeric(step6_df[column], errors="coerce").fillna(0)
show_step("6단계. 숫자 컬럼 타입 변환", "숫자 변환이 불가능한 값은 0으로 처리했습니다.", step6_df)

step7_df = step6_df.copy()
step7_df["estimated_salary_total"] = step7_df["charge_amount"] / 0.095
step7_df["estimated_salary_per"] = (
    step7_df["estimated_salary_total"]
    .div(step7_df["member_count"].replace(0, pd.NA))
    .fillna(0)
)
step7_df["net_change"] = step7_df["new_members"] - step7_df["lost_members"]
show_step("7단계. 파생 컬럼 생성", "추정 급여 총액, 1인당 추정 급여, 순증감 컬럼을 생성했습니다.", step7_df)

step8_df = step7_df.loc[
    (step7_df["status"] == "등록")
    & (step7_df["member_count"] > 0)
    & (step7_df["charge_amount"] > 0)
].copy()
show_step(
    "8단계. 이상값 처리",
    f"등록 상태이며 가입자 수와 고지 금액이 0보다 큰 행만 유지했습니다. {len(step8_df):,}행이 남았습니다.",
    step8_df,
)

cleaned_df = step8_df.reset_index(drop=True)
os.makedirs(DATA_DIR, exist_ok=True)
cleaned_df.to_csv(OUTPUT_PATH, encoding="utf-8", index=False)
show_step(
    "9단계. 전처리 결과 저장",
    f"전처리된 데이터를 `{OUTPUT_PATH}`에 저장했습니다.",
    cleaned_df,
)

before_metric.metric("전처리 전", f"{source_row_count:,}행")
after_metric.metric("전처리 후", f"{len(cleaned_df):,}행")

st.subheader("전처리 데이터 기본 통계")
total_companies = len(cleaned_df)
total_sidos = cleaned_df["sido"].nunique()
total_members = cleaned_df["member_count"].sum()
average_salary_per_member = (
    cleaned_df["estimated_salary_per"].mean() if not cleaned_df.empty else 0
)
company_metric, sido_metric, member_metric, salary_metric = st.columns(4)
company_metric.metric("총 사업장 수", f"{total_companies:,}")
sido_metric.metric("시도 수", f"{total_sidos:,}")
member_metric.metric("총 가입자 수", f"{total_members:,.0f}")
salary_metric.metric("전체 1인당 추정 평균 월급여", f"{average_salary_per_member:,.0f}원")
