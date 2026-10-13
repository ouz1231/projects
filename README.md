# Old Faithful 분출 패턴 대시보드

seaborn의 geyser 데이터를 사용해 분출시간과 다음 대기시간의 관계를 탐색하는 Streamlit 대시보드입니다. 유형 필터, 시간 범위 슬라이더, Seaborn/Plotly 산점도 전환, 분포·그룹 비교, CSV 다운로드를 제공합니다.

## 실행

```bash
uv sync
uv run streamlit run geyser.py
```

pip 환경에서는 `pip install -r requirements.txt` 후 `streamlit run geyser.py`를 실행하세요.

## 데이터

앱은 `seaborn.load_dataset("geyser")`를 먼저 시도하고, 네트워크 연결이 실패하면 `data/geyser.csv`를 사용합니다. 데이터는 분출시간(`duration`, 분), 대기시간(`waiting`, 분), 유형(`kind`)으로 구성된 272회 Old Faithful 관측입니다.

## Streamlit Community Cloud

GitHub 저장소를 연결하고 앱 파일 경로를 `geyser.py`로 지정하세요. Cloud는 `requirements.txt`를 통해 의존성을 설치하며, 백업 데이터와 테마는 저장소에 포함되어 있습니다.
