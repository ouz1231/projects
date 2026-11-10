import pandas as pd

df = pd.read_csv("data/pension_raw.csv", encoding="cp949")

print("첫 다섯 행:")
print(df.head())

print("\n컬럼 이름:")
print(df.columns.tolist())

print("\n컬럼별 데이터 타입:")
print(df.dtypes)

print(f"\n전체 행 수: {df.shape[0]}")
print(f"전체 컬럼 수: {df.shape[1]}")

print("\n컬럼별 결측값 개수:")
print(df.isna().sum())

print(f"\n전체 결측값 개수: {df.isna().sum().sum()}")