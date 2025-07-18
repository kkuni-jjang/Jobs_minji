'''
부트갬프 모델링 로직 모듈
'''
import pandas as pd
import ast
from sqlalchemy import create_engine        
from gap_model import extract_top_gap_items, get_trend_skills_by_category

# === 유저 스킬 조회 ===
def get_user_skills_with_proficiency(user_id: int, engine):
    query = f"""
    SELECT
        s.name AS skill_name
    FROM user_skills us
    JOIN skills s ON s.id = us.skill_id
    WHERE us.user_id = {user_id};
    """
    return pd.read_sql(query, engine)

# [2] 최종 스킬 점수 계산
def score_skills(user_skills: list, top_skills: list, skill_order: list) -> pd.DataFrame:
    user_skills = set(s.lower() for s in user_skills)
    top_skills = set(s.lower() for s in top_skills)
    skill_order = [s.lower() for s in skill_order]

    # 1. 유저가 안 가진 추천 스킬 → except_skills
    except_skills = user_skills - top_skills

    # 2. except_skills 중 skill_order에 포함된 것 → unmatched
    unmatched_skills = [s for s in skill_order if s in except_skills]

    # 3. unmatched 제외한 최종 스킬 리스트
    final_skill = [s for s in skill_order if s not in unmatched_skills]


    # 4. 점수 계산
    base_score = len(final_skill)
    scored_skills = []
    for i, skill in enumerate(final_skill):
        base = base_score - i
        bonus = 5 if skill in top_skills else 0
        total_score = base + bonus
        scored_skills.append({
            "skill": skill,
            "base_score": base,
            "bonus": bonus,
            "total_score": total_score
        })

    
    scored_df = pd.DataFrame(scored_skills).sort_values(by="total_score", ascending=False).reset_index(drop=True)
    return scored_df


# [3] 로드맵 점수화 적용 함수
def apply_score_to_roadmaps(roadmaps: pd.DataFrame, scored_df: pd.DataFrame) -> pd.DataFrame:
    # 스킬-점수 매핑
    skill_score_map = dict(zip(scored_df["skill"], scored_df["total_score"]))

    # 점수 계산 함수
    def calculate_score(skill_list):
        normalized = [s.lower().strip() for s in skill_list]
        return sum(skill_score_map.get(skill, 0) for skill in normalized)

    # 문자열로 되어 있으면 파싱
    if roadmaps["skill_description"].apply(type).eq(str).any():
        roadmaps["skill_description"] = roadmaps["skill_description"].apply(ast.literal_eval)

    # 점수 계산 및 정렬
    roadmaps["skill_score"] = roadmaps["skill_description"].apply(calculate_score)
    return roadmaps.sort_values(by="skill_score", ascending=False).reset_index(drop=True)




# 3. 메인 로직 함수 (FastAPI에서 호출)
def roadmap_recommendation(user_id: int, category: str, top_skills: list, gap_result_text: str, engine) -> pd.DataFrame:
    # 유저 보유 스킬
    df_skills = get_user_skills_with_proficiency(user_id, engine)
    user_skills = df_skills["skill_name"].str.lower().tolist()

     # 상위 직무에 따른 스킬 트렌드
    from gap_model import get_trend_skills_by_category  # 외부 함수 불러오기
    skill_order = get_trend_skills_by_category(category, engine)

    scored_df = score_skills(user_skills, top_skills, skill_order)

    # 로드맵 로드
    roadmaps = pd.read_sql("SELECT * FROM roadmaps", engine)
    scored_roadmaps = apply_score_to_roadmaps(roadmaps, scored_df)

    return scored_roadmaps


######################### 백엔드 실행 영역 #########################
from bootcamp_model import roadmap_recommendation
from gap_model import extract_top_gap_items
from db import get_engine
from fastapi import FastAPI
app = FastAPI()

@app.get("/recommendation/")
def get_roadmap(user_id: int, category: str, gap_result_text: str):
    top_skills = extract_top_gap_items(gap_result_text)
    engine = get_engine()
    result = roadmap_recommendation(user_id, category, top_skills, gap_result_text, engine)
    return result.to_dict(orient="records")