'''
데이터불러오기 
'''
import pandas as pd
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# .env 파일의 경로를 명시적으로 지정
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

def get_engine():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db = os.getenv("DB_NAME")

    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    return create_engine(url)


# 유저 데이터 불러오기
def load_user_data(user_id: int, engine) -> dict:
    query = f"""
    SELECT 
        u.id,
        u.name,
        u.gender,
        u.university,
        u.major,
        u.education_status,
        u.degree,
        u.language_score,
        u.desired_job,

        ue.name AS experience_name,
        ue.period AS experience_period,
        ue.description AS experience_description,

        s.name AS skill_name,
        us.proficiency AS skill_proficiency,

        c.name AS certificate_name

    FROM "Users" u
    LEFT JOIN "UserExperience" ue ON u.experience_id = ue.id
    LEFT JOIN "User_Skill" us ON u.id = us.user_id
    LEFT JOIN "Skill" s ON us.skill_id = s.id
    LEFT JOIN "User_Certificate" uc ON uc.user_id = u.id
    LEFT JOIN "Certificate" c ON uc.certificate_id = c.id

    WHERE u.id = {user_id}
    """
    df = pd.read_sql(query, engine)

    # 기본 유저 정보
    user_base = df.iloc[0][[
        "id", "name", "gender", "university", "major", "education_status",
        "degree", "language_score", "desired_job"
    ]].to_dict()
    
    # JSON 처리
    import json
    try:
        user_base["language_score"] = json.loads(user_base["language_score"])
    except:
        user_base["language_score"] = {}

    # 경험
    experience = {
        "name": df.iloc[0]["experience_name"],
        "period": df.iloc[0]["experience_period"],
        "description": df.iloc[0]["experience_description"]
    }

    # 스킬
    skills_df = df[["skill_name", "skill_proficiency"]].dropna().drop_duplicates()
    skill_names = skills_df["skill_name"].tolist()
    proficiencies = skills_df["skill_proficiency"].tolist()

    # 자격증
    certificates = df["certificate_name"].dropna().drop_duplicates().tolist()

    return {
        **user_base,
        "experience": [experience],
        "skill_id": skill_names,
        "proficiency": proficiencies,
        "certificate_id": certificates
    }


# 공고 데이터 불러오기
def load_job_data(engine) -> pd.DataFrame:
    query = """
    SELECT id, company_name, title, full_embedding, main_tasks, qualifications, preferences, tech_stack
    FROM job_postings
    """
    return pd.read_sql(query, engine)