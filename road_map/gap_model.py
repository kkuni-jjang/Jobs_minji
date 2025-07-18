'''
갭차이 분석 모델 모듈
    - category: 프론트에서 받은 직무 카테고리
'''
import os
import pandas as pd
import re
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

# OpenAI 클라이언트 초기화 (API 키는 .env에서 로드됨)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# 트렌드 스킬 리스트 조회 함수
def get_trend_skills_by_category(category: str, engine: Engine) -> list:
    query = f"""
    SELECT wss.skill, jrs.job_name, SUM(wss.count) AS total_count
    FROM weekly_skill_stats wss
    JOIN job_required_skills jrs ON wss.job_role_id = jrs.id
    WHERE jrs.job_name = '{category}'
    GROUP BY wss.skill, jrs.job_name
    ORDER BY total_count DESC;
    """
    df = pd.read_sql(query, engine)
    return df["skill"].tolist()


# 유저 정보 조회 함수
def get_user_summary(user_id: int, engine: Engine) -> pd.DataFrame:
    query = f"""
    SELECT
        u.id AS user_id,
        u.name,
        u.gender,
        u.university,
        u.major,
        u.degree,
        u.education_status,
        u.desired_job,
        u.language_score ->> 'OPIC' AS opic_score,

        STRING_AGG(DISTINCT s.name || '(' || us.proficiency || ')', ', ') AS skills_with_proficiency,
        STRING_AGG(DISTINCT c.name, ', ') AS certificates,

        COALESCE(e.name, '없음') AS latest_exp_name,
        COALESCE(e.period, '없음') AS latest_exp_period,
        COALESCE(e.description, '없음') AS latest_exp_description

    FROM users u
    LEFT JOIN user_skills us ON us.user_id = u.id
    LEFT JOIN skills s ON s.id = us.skill_id
    LEFT JOIN user_certificates uc ON uc.user_id = u.id
    LEFT JOIN certificates c ON c.id = uc.certificate_id
    LEFT JOIN LATERAL (
        SELECT name, period, description
        FROM user_experiences
        WHERE user_id = u.id
        ORDER BY period DESC
        LIMIT 1
    ) e ON true

    WHERE u.id = {user_id}

    GROUP BY 
        u.id, u.name, u.gender, u.university, u.major, 
        u.degree, u.education_status, u.desired_job,
        e.name, e.period, e.description;
    """
    return pd.read_sql(query, engine)


# 갭 분석 프롬프트 생성 함수
def make_gap_analysis_prompt(user_data: dict, skill_trend: list, job_category: str) -> str:
    name = user_data['name']
    major = user_data['major']
    university = user_data['university']
    degree = user_data['degree']
    education_status = user_data['education_status']
    desired_jobs = ', '.join(user_data['desired_job']) if isinstance(user_data['desired_job'], list) else user_data['desired_job']
    opic_score = user_data.get('opic_score') or "없음"
    skills = user_data['skills_with_proficiency']
    certs = user_data['certificates']
    exp_name = user_data['latest_exp_name']
    exp_period = user_data['latest_exp_period']
    exp_desc = user_data['latest_exp_description']

    return f"""
당신은 채용 담당자를 위한 커리어 갭 분석 전문가입니다.

[지원자 정보]
이름: {name}
학교: {university}, 전공: {major}
학위: {degree}, 학력 상태: {education_status}
어학 점수 (OPIC): {opic_score}
기술 스택 (숙련도 포함): {skills}
자격증: {certs}
경험: {exp_name} / 기간: {exp_period}
경험 설명: {exp_desc}

[기준 역량 리스트]
다음은 최근 **{job_category}** 직무에서 요구되는 주요 역량 리스트입니다.
이 리스트에는 기술 스택 뿐만 아니라, 협업 경험, 프로젝트 운영, 문서화 능력, 서비스 개선 등
**비기술적/경험 기반 역량**도 포함되어 있습니다:
{', '.join(skill_trend)}

[요청사항]
위 기준 역량 리스트를 상단부터 순서대로 확인하며, 지원자와의 격차를 분석해 주세요.

분석 순서는 다음과 같습니다:
1. 기준 역량 리스트 상단에 있을수록 **우선순위가 높습니다**.  
       반드시 리스트 순서를 기준으로 분석해주세요.
2. 각 항목마다 **지원자 보유 여부 및 숙련도(하/중/상)**를 참고해 격차를 판단해 주세요.
        단, **리스트 순서를 벗어난 재정렬은 하지 마세요**.
3. 보유 여부/숙련도에 따른 격차 판단 기준은 다음과 같습니다:
   - **보유하지 않은 경우** → 격차가 가장 큽니다.
   - **보유했지만 숙련도 '하'** → 그 다음 격차입니다.
   - **숙련도 '중'** → 상대적으로 덜한 격차입니다.
   - **숙련도 '상'**은 격차로 판단하지 않습니다.

아래 형식에 따라 상위 5개의 격차 항목만 출력해 주세요:

보유여부, 숙련도는 이력서 기반 판단해주세요.

[역량 이름]
- 현재 보유 여부: 있음 / 없음
- 숙련도: 없음 / 하 / 중 / 상
- 필수 여부: 필수 / 선택
- 사유: 
  - 지원자가 보유했다면 **경험 기반 숙련도**를 참고해 부족한 이유를 설명해 주세요.
  - 보유하지 않았다면, 해당 역량이 왜 중요한지 간결하고 명확하게 (2~3줄 이내로) 설명해 주세요.

협업 경험 / 프로젝트 경험 / 운영 경험 등은 **경험 설명에 해당 키워드가 있거나 팀 기반 활동이면 있음으로 간주**해 주세요.  
예를 들어 "사내 API 개발 및 유지보수"는 협업이 포함된 활동입니다.

**비기술 역량도 중요**하니 기술 스택 외 항목도 반드시 포함하여 평가해 주세요.
"""


# LLM 호출 함수
def call_llm_for_gap_analysis(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "당신은 채용 담당자를 위한 커리어 갭 분석 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content 


# 역량 이름 리스트 추출 함수
def extract_top_gap_items(response_text: str) -> list:
    return re.findall(r'\d+\.\s\*\*(.+?)\*\*', response_text)


# 갭 분석 함수
def perform_gap_analysis(user_id: int, category: str, engine: Engine) -> dict:
    skill_order = get_trend_skills_by_category(category, engine)
    skill_trend = skill_order[:20]  # 상위 20개만 사용

    user_df = get_user_summary(user_id, engine)
    if user_df.empty:
        raise ValueError(f"User {user_id} not found")

    user_data = user_df.iloc[0].to_dict()
    prompt = make_gap_analysis_prompt(user_data, skill_trend, category)
    gap_result_text = call_llm_for_gap_analysis(prompt)
    top_skills = extract_top_gap_items(gap_result_text)

    return {
        "user_id": user_id,
        "category": category,
        "gap_result": gap_result_text,
        "top_skills": top_skills
    }

