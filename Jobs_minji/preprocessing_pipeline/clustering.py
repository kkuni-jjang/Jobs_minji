# job_postings_with_embeddings.json 파일을 클러스터링 파이프라인에 적용
# -----------------------------
import json
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from collections import Counter
from typing import List
from tqdm.auto import tqdm
import re

# ===== 설정 =====
INPUT_PATH = "job_postings_with_embeddings.json"
OUTPUT_PATH = "job_postings_with_clustered.json"
N_CLUSTERS = 200

# ===== 유틸 함수 =====
def load_jobs_with_embeddings(path: str):
    with open(path, "r", encoding="utf-8") as f:
        jobs = json.load(f)
    embeddings = np.array([job["full_embedding"] for job in jobs])
    return jobs, embeddings

def save_jobs(jobs, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

def split_job_category(category_str):
    if pd.isna(category_str) or not category_str.strip():
        return []

    tokens = []
    buffer = ""
    parts = re.split(r'(,)', category_str)

    i = 0
    while i < len(parts):
        part = parts[i]
        if part == ',':
            if i + 1 < len(parts) and not parts[i + 1].startswith(' '):
                buffer += ',' + parts[i + 1]
                i += 2
            else:
                tokens.append(buffer.strip())
                buffer = ""
                i += 1
        else:
            buffer += part
            i += 1

    if buffer:
        tokens.append(buffer.strip())

    return tokens
  
def get_priority_dict(jobs) -> dict:
    all_categories = []
    for job in jobs:
        all_categories.extend(split_job_category(job.get("job_category", "")))
    counts = Counter(all_categories)
    return {k: i for i, (k, _) in enumerate(counts.most_common())}

def get_representative_category(category_list: List[str], priority_dict: dict):
    filtered = [cat for cat in category_list if cat in priority_dict]
    if not filtered:
        return None
    return sorted(filtered, key=lambda x: priority_dict[x])[0]

# ===== 클러스터링 파이프라인 =====
def run_clustering_pipeline():
    print("데이터 로드 중...")
    jobs, embeddings = load_jobs_with_embeddings(INPUT_PATH)

    print(f"클러스터링 수행 중 (n_clusters={N_CLUSTERS})...")
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init="auto")
    cluster_labels = kmeans.fit_predict(embeddings)

    print("대표 직무 추출 중...")
    df = pd.DataFrame(jobs)
    df["cluster"] = cluster_labels
    df["job_category_list"] = df["job_category"].apply(split_job_category)

    priority_dict = get_priority_dict(jobs)

    rep_categories = []
    for cluster_id in tqdm(range(N_CLUSTERS), desc="클러스터 대표 직무 지정"):
        group = df[df["cluster"] == cluster_id]
        merged = []
        for item in group["job_category_list"]:
            merged.extend(item)
        rep = get_representative_category(merged, priority_dict)
        rep_categories.append((cluster_id, rep))

    rep_dict = {cid: rep for cid, rep in rep_categories}

    df["job_category"] = df["cluster"].map(rep_dict)
    df.drop(columns=["job_category_list"], inplace=True)

    # 원래 jobs 리스트에 cluster와 job_category 덮어쓰기
    for i, row in df.iterrows():
        jobs[i]["cluster"] = int(row["cluster"])
        jobs[i]["job_category"] = row["job_category"]

    save_jobs(jobs, OUTPUT_PATH)
    print(f"클러스터링 완료! 저장됨: {OUTPUT_PATH}")

# ===== 실행 엔트리포인트 =====
if __name__ == "__main__":
    run_clustering_pipeline()