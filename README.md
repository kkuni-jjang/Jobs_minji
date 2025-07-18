# Jobs_minji

채용 공고 데이터 전처리 및 분석 파이프라인

## 프로젝트 구조

```
Jobs_minji/
├── mongo.py                    # MongoDB 연결 및 데이터 처리
├── preprocessing_pipeline/     # 데이터 전처리 파이프라인
│   ├── clustering.py          # 데이터 클러스터링
│   ├── embedding.py           # 텍스트 임베딩 생성
│   ├── tokenizer.py           # 키워드 추출 및 토큰화
│   ├── send_postgre.py        # PostgreSQL 데이터 저장
│   ├── requirements.txt       # 의존성 패키지
│   └── data/                  # 전처리된 데이터
└── road_map/                  # 로드맵 관련 모델
    ├── bootcamp_model.py      # 부트캠프 모델
    ├── gap_model.py           # 갭 분석 모델
    └── routing.py             # 라우팅 로직
```

## 설치 및 실행

1. 의존성 설치:
```bash
cd preprocessing_pipeline
pip install -r requirements.txt
```

2. 데이터 전처리 파이프라인 실행:
```bash
python embedding.py      # 임베딩 생성
python clustering.py     # 클러스터링
python tokenizer.py      # 키워드 추출
python send_postgre.py   # PostgreSQL 저장
```

## 주요 기능

- **데이터 임베딩**: 채용 공고 텍스트를 벡터로 변환
- **클러스터링**: 유사한 채용 공고들을 그룹화
- **키워드 추출**: 주요 기술 스택 및 요구사항 추출
- **데이터베이스 저장**: PostgreSQL에 정제된 데이터 저장

## 환경 설정

PostgreSQL 연결 정보는 `send_postgre.py`에서 설정:
- Host: 192.168.101.51
- Port: 5432
- Database: jobs
- User: myuser
- Password: mypassword 