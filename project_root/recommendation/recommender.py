from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

# 1. 임베딩 모델 로드 (E5)
embedder = SentenceTransformer("intfloat/multilingual-e5-large")


# 2. 유저 텍스트 요약 (임베딩용)
def summarize_user_for_embedding(user: dict) -> str:
    skills = [f"{s}({l})" for s, l in zip(user.get("skill_id", []), user.get("proficiency", []))]
    skill_part = ", ".join(skills) if skills else "없음"
    cert_part = ", ".join(user.get("certificate_id", [])) or "없음"

    exp = user.get("experience", [{}])[0]
    if exp:
        exp_text = f"{exp.get('name', '')}, {exp.get('period', '')}, {exp.get('description', '')}"
    else:
        exp_text = "없음"

    return (
        f"이름: {user['name']}\n"
        f"성별: {user['gender']}, 학교: {user['university']}, 학과: {user['major']}, "
        f"학위: {user['degree']}, 학력 상태: {user['education_status']}\n"
        f"희망 직무: {user['desired_job']}\n"
        f"어학 점수: {user.get('language_score', {}).get('OPIC', '없음')}\n"
        f"기술 스택: {skill_part}\n"
        f"자격증: {cert_part}\n"
        f"경험: {exp_text}"
    )


# 3. 유저 임베딩 생성
def get_user_embedding(user_dict: dict) -> np.ndarray:
    user_text = summarize_user_for_embedding(user_dict)
    embedding = embedder.encode(user_text, normalize_embeddings=True)
    if hasattr(embedding, "numpy"):
        embedding = embedding.numpy()
    embedding = np.array(embedding)
    return embedding


# 4. 유사도 기반 추천
def get_top_n_jobs(user_embedding: np.ndarray, jobs_df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    if "full_embedding" not in jobs_df.columns:
        raise ValueError("❗ jobs_df에 'full_embedding' 컬럼이 없습니다.")

    job_embeddings = np.vstack(jobs_df["full_embedding"].tolist())
    sims = cosine_similarity([user_embedding], job_embeddings)[0]
    jobs_df = jobs_df.copy()
    jobs_df["similarity"] = sims
    return jobs_df.sort_values(by="similarity", ascending=False).head(n)
