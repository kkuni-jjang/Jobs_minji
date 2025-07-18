import json
import re
import pandas as pd
from tqdm.auto import tqdm
from transformers import AutoTokenizer

# 1. 데이터 불러오기
input_path =  "Jobs_minji\preprocessing_pipeline\data\preprocessed_jobs_20250716_015908.json"
output_path = "Jobs_minji\preprocessing_pipeline\data"
data = pd.read_json(input_path)

# 2. E5 tokenizer 로드
tokenizer = AutoTokenizer.from_pretrained("intfloat/multilingual-e5-large")

# 3. 토큰화 + 단어 복원 함수
def tokenize_and_recover_words(text):
    if pd.isna(text):
        return []
    tokens = tokenizer.tokenize(text)
    recovered = tokenizer.convert_tokens_to_string(tokens)
    return recovered.split()



# 4. 정제 함수
def clean_word_list(word_list):
    cleaned = []
    for word in word_list:
        word = re.sub(r"[^\w가-힣/]", "", word)  # 특수문자 제거
        if "/" in word:
            parts = word.split("/")
            cleaned.extend([w.strip().lower() for w in parts if w.strip()])
        else:
            word = word.strip().lower()
            if word:
                cleaned.append(word)
    return cleaned

# 5. tqdm 설정
tqdm.pandas()

# 6. 컬럼별 토큰화 + 정제 적용
data["main_tasks_skills"] = data["main_tasks"].progress_apply(tokenize_and_recover_words).apply(clean_word_list)
data["required_skills"] = data["qualifications"].progress_apply(tokenize_and_recover_words).apply(clean_word_list)
data["preferred_skills"] = data["preferences"].progress_apply(tokenize_and_recover_words).apply(clean_word_list)

# 7. 결과 확인
print(data[["id", "main_tasks_skills", "required_skills", "preferred_skills"]].head())

# 8. 저장
data.to_json(output_path, orient="records", force_ascii=False)

