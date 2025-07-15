import os
from dotenv import load_dotenv

from recommendation.db import get_engine, load_user_data, load_job_data
from recommendation.recommender import (
    get_user_embedding,
    get_top_n_jobs,
    summarize_user_for_embedding,
)
from recommendation.llm_recommender import call_qwen_api, make_prompt, summarize_user_text

# 🔐 .env에서 API 키 로드
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")  # 꼭 환경변수명 바꿔야 함!

# 1️⃣ DB 연결 및 데이터 로드
engine = get_engine()
user_dict = load_user_data(user_id=2, engine=engine)
jobs_df = load_job_data(engine)

# 2️⃣ 유저 임베딩 생성
user_embedding = get_user_embedding(user_dict)

# 3️⃣ Top 30개 공고 추출 (유사도 기반)
top_jobs = get_top_n_jobs(user_embedding, jobs_df, n=30)

# 4️⃣ 프롬프트 생성
user_summary = summarize_user_text(user_dict)
llm_prompt = make_prompt(user_summary, top_jobs.to_dict(orient="records"))

# 5️⃣ LLM 호출 (Qwen via OpenRouter)
response_text = call_qwen_api(llm_prompt, api_key)

# 6️⃣ 결과 출력
print("\n📌 최종 추천 결과:\n")
print(response_text)
