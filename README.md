# ChartMind AI v5 (교육용 모의 분석)

## Render 설정
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Plan: Free
- Environment Variables: 필수 항목 없음

## 주요 기능
- 암호화폐와 미국/한국 주요 주식 선택
- Binance 공개 API 및 Yahoo Finance 차트 데이터로 캔들 그래프 표시
- 검정색 UI, 상승 캔들 초록색 / 하락 캔들 빨간색
- SMA20, SMA50, RSI(14), 최근 봉 변화 표시
- 규칙 기반 5개 분석 역할과 최종 판단 근거
- 5~60초 자동 갱신 설정, 자동 갱신 중지, 즉시 갱신
- 뉴스 제목 검색(가능한 경우)

## 한계와 비용
- 이 버전은 생성형 AI API를 호출하지 않으며 API 키가 필요 없습니다.
- 5개 역할은 별도의 생성형 AI 에이전트가 아니라 설명 가능한 규칙 기반 모듈입니다.
- 실제 주식/코인 주문, 거래소 연결, 실계좌 접근 기능은 없습니다.
- 공개 시세 API는 제공처의 정책/네트워크/요청 제한에 따라 지연되거나 실패할 수 있습니다.
- Render Free는 비활성 시 잠들 수 있어 처음 접속이 느릴 수 있습니다.
- Render 유료 플랜으로 업그레이드하지 마세요. 필수 유료 API도 없습니다.
