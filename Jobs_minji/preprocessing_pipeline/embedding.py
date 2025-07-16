# 임베딩 파이프라인
import json
import numpy as np
from tqdm.auto import tqdm
from sentence_transformers import SentenceTransformer

# ===== 설정 =====
JOBS_PATH = 'preprocessed_jobs_20250716_015908.json'
OUTPUT_PATH = 'job_postings_with_embeddings.json'
MODEL_NAME = "intfloat/multilingual-e5-large"
BATCH_SIZE = 64
MAIN_TASKS_WEIGHT = 2
QUALIFICATIONS_WEIGHT = 2

# ===== 텍스트 생성 함수 =====
def job_to_text(job, main_tasks_weight=2, qualifications_weight=2):
    main_tasks = (job.get('main_tasks') or '').strip()
    qualifications = (job.get('qualifications') or '').strip()
    preferences = (job.get('preferences') or '').strip()
    tech_stack = (job.get('tech_stack') or '').strip()

    main_tasks_repeated = (main_tasks + "\n") * main_tasks_weight
    qualifications_repeated = (qualifications + "\n") * qualifications_weight

    return (
        f"직무명: {job.get('job_category', '')}\n"
        f"고용형태: {job.get('employment_type', '')}, 지원대상: {job.get('applicant_type', '')}\n"
        f"주요업무: {main_tasks_repeated}"
        f"자격요건: {qualifications_repeated}"
        f"우대사항: {preferences}\n"
        f"기술스택: {tech_stack}"
    )

# ===== 임베딩 함수 =====
def embed_jobs(jobs, model_name, batch_size):
    model = SentenceTransformer(model_name)
    texts = [job_to_text(job, MAIN_TASKS_WEIGHT, QUALIFICATIONS_WEIGHT) for job in jobs]
    all_embeddings = []

    for i in tqdm(range(0, len(texts), batch_size), desc=f"임베딩 진행중 ({model_name})"):
        batch_texts = texts[i:i + batch_size]
        embs = model.encode(
            batch_texts,
            batch_size=batch_size,
            convert_to_numpy=True
        )
        all_embeddings.append(embs)

    return np.vstack(all_embeddings)

# ===== 메인 실행 함수 =====
def run_embedding_pipeline():
    with open(JOBS_PATH, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    embeddings = embed_jobs(jobs, MODEL_NAME, BATCH_SIZE)

    assert len(jobs) == len(embeddings), "공고 수와 임베딩 수가 다릅니다!"

    for i in range(len(jobs)):
        jobs[i]["full_embedding"] = embeddings[i].tolist()

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    print(f"임베딩 완료 및 저장: {OUTPUT_PATH}")


# 실행
if __name__ == "__main__":
    run_embedding_pipeline()