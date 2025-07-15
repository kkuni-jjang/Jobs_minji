'''
llm api로 재랭킹 파일
'''
import openai
import os
from typing import List, Dict
import requests

def summarize_user_text(user: Dict) -> str:
    # 기술 스택 정리
    skills = [f"{skill}({level})" for skill, level in zip(user.get("skill_id", []), user.get("proficiency", []))]
    skill_part = ", ".join(skills) if skills else "없음"

    # 자격증 정리
    certs = user.get("certificate_id", [])
    cert_part = ", ".join(certs) if certs else "없음"

    # 경험 정리
    exp_list = user.get("experience", [])
    if exp_list:
        exp = exp_list[0]
        exp_text = f"{exp['name']} ({exp['period']}): {exp['description']}"
    else:
        exp_text = "없음"

    summary = (
        f"이름: {user['name']}\n"
        f"성별: {user['gender']}, 학교: {user['university']}, 학과: {user['major']}, "
        f"학위: {user['degree']}, 학력 상태: {user['education_status']}\n"
        f"희망 직무: {user['desired_job']}\n"
        f"어학 점수: {user.get('language_score', {}).get('OPIC', '없음')}\n"
        f"기술 스택: {skill_part}\n"
        f"자격증: {cert_part}\n"
        f"경험: {exp_text}"
    )
    return summary

def make_prompt(user_summary: str, job_list: List[Dict]) -> str:
    job_str_list = []
    for job in job_list:
        job_str_list.append(
            f"공고 ID: {job['id']}\n직무명: {job['title']}\n주요 업무: {job['main_tasks']}\n자격 요건: {job['qualifications']}\n우대 사항: {job['preferences']}\n기술 스택: {job['tech_stack']}\n"
        )
    jobs_text = "\n---\n".join(job_str_list)

    prompt = (
        "다음은 신입 데이터 분석가의 상세 이력과 채용 공고 30개입니다.\n\n"
        "[지원자 정보]\n"
        f"{user_summary}\n\n"
        "[요청사항]\n"
        "- 아래 채용 공고 목록은 **지원자와의 유사도 순으로 정렬된 상태**입니다. 상위 공고일수록 우선적으로 검토해 주세요.\n"
        "- 아래 공고 중 **지원자가 현실적으로 지원할 수 없는 자격 요건**(예: 전문연구요원, 병역특례, 경력 1년 이상 등)을 포함한 공고는 제외해 주세요.\n"
        "  단, '지원 가능' 등의 예외 문구가 명시된 경우는 포함 가능합니다.\n"
        "- 지원자의 기술 스택은 **숙련도(상/중/하)** 정보가 포함되어 있습니다. 이를 기반으로 다음과 같이 **가중치를 적용해 매칭**해 주세요:\n"
        "  - 숙련도: 상 = 3점 / 중 = 2점 / 하 = 1점\n"
        "- 단순 조건 충족이 아니라, **실제로 잘 맞는 공고** 5개를 추천해 주세요.\n"
        "- 각 추천 공고에 대해 아래 3가지를 작성해 주세요:\n"
        "  1) 적합한 이유 (지원자의 정보와 일치, 예: 지원자 정보, 기술스택 등 )\n"
        "  2) 부족하거나 충족하지 못한 부분이 있다면 구체적으로 작성\n\n"
        "[채용 공고 목록]\n"
        f"{jobs_text}\n\n"
        "위 목록에서 가장 적합한 5개 공고를 아래 형식으로 출력해 주세요:\n"
        "- 공고 ID\n"
        "- 직무명\n"
        "- 적합 이유\n"
        "- 부족한 부분\n"
    )
    return prompt

def call_qwen_api(prompt, api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site.com",  
        "X-Title": "Job Recommender"
    }
    body = {
        "model": "qwen/qwq-32b:free",  
        "messages": [
            {"role": "system", "content": "너는 채용 공고 추천 전문가야."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
        "max_tokens": 4096
    }

    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]