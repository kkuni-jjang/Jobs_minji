import json
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text


# 상대방 PostgreSQL 정보 #.env 파일에서 가져오기
host = "192.168.101.51"   
port = "5432"
user = "myuser"
password = "mypassword"
database = "jobs"

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")

#== 데이터 가져오기 ==
# 1. clustering.py 에서 임베딩된 'clustered_data.json' 가져오기
'''
이때, 데이터는 임베딩된 데이터이며, 데이터 형식은 다음과 같다.
['id', 'title', 'company_name', 'size', 'address', 'job_category','employment_type', 
'applicant_type', 'posting_date', 'deadline', 'main_tasks', 'qualifications', 
'preferences', 'tech_stack','full_embedding', 'cluster']
'''
clustered_data = pd.read_json('clustered_data.json')
clustered_data = pd.DataFrame(clustered_data) 

# 2. tokenizer.py 에서 'keyword_data.json' 가져오기
'''
이때, 데이터는 키워드 데이터이며, 데이터 형식은 다음과 같다.
['id', 'main_tasks_skills', 'required_skills', 'preferred_skills']
'''
keyword_data = pd.read_json('keyword_data.json')
keyword_data = pd.DataFrame(keyword_data) 

# 3. 직무 카테고리 데이터 {PostgreSQL} 에서 'job_required_skills' 테이블 가져오기
'''
이때, 데이터는 직무 카테고리 데이터이며, 데이터 형식은 다음과 같다.
['id', 'job_name']
'''
job_required_skills = pd.read_sql("SELECT id, job_name FROM job_required_skills", engine)  


#== 데이터 전처리 ==
'''
최종 데이터 형식은 다음과 같다.
['id', 'title', 'company_name', 'size', 'address', 'job_required_skill_id', 
'employment_type', 'applicant_type', 'posting_date', 'deadline', 'main_tasks', 
'qualifications', 'preferences', 'tech_stack', 'created_at', 'required_skills',
'preferred_skills', 'main_tasks_skills', 'full_embedding']
'''

# 1. clustered_data 와 keyword_data 를 병합하여 {merged_data} 데이터 프레임 생성
'''
'required_skills', 'preferred_skills', 'main_tasks_skills' 컬럼 추가
'''
merged_data = clustered_data.merge(keyword_data, on='id', how='left')

# 2. merged_data 와 job_required_skills 를 조인하여 {final_data} 데이터 프레임 생성
'''
이때, merged_data 의 'job_category' 컬럼과 job_required_skills 의 'job_name' 컬럼을 조인하여
'job_required_skill_id' 컬럼 추가
'''
## a. 컬럼명 통일 (job_required_skills 테이블)
job_required_skills.rename(columns={"id": "job_required_skill_id",'job_name': 'job_category'}, inplace=True)

## b. 조인
join_data = merged_data.merge(job_required_skills[["job_category", "job_required_skill_id"]], on='job_category', how='left')

# 3. join_data 를 후처리하여 {final_data} 데이터 프레임 생성
## a. 불필요한 컬럼 제거
join_data.drop(columns=["job_category", "cluster"], inplace=True, errors="ignore")

## b. jsonb 형식으로 변환
for col in ["required_skills", "preferred_skills", "main_tasks_skills"]:
    join_data[col] = join_data[col].apply(json.dumps)

## c. 컬럼 순서 재정렬  
target_columns = [
    'id', 'title', 'company_name', 'size', 'address',
    'job_required_skill_id',  
    'employment_type', 'applicant_type', 'posting_date', 'deadline',
    'main_tasks', 'qualifications', 'preferences', 'tech_stack', 
    'required_skills', 'preferred_skills', 'main_tasks_skills', 'full_embedding'
]
final_data = join_data[target_columns]

## d. address 결측치 처리
join_data["address"] = join_data["address"].fillna("")

# 4. 중복검사   
## a. 현재 DB에 존재하는 id 목록 가져오기
with engine.connect() as conn:
    existing_ids = pd.read_sql(text("SELECT id FROM job_posts"), conn)
    existing_ids_set = set(existing_ids['id'])

## b. 중복되지 않은 데이터만 필터링
mask = ~final_data['id'].isin(list(existing_ids_set))
final_data = final_data[mask]

# 5. {PostgreSQL} 에 'job_posts' 테이블에 데이터 저장
final_data.to_sql('job_posts', engine, if_exists='append', index=False)






