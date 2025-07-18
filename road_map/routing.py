from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from .service import perform_gap_analysis
from app.database import get_db  # 🔁 너희 프로젝트에 맞게 import 수정

router = APIRouter()

@router.get("/gap-analysis", response_class=JSONResponse)
def gap_analysis_endpoint(
    user_id: int = Query(..., description="분석 대상 사용자 ID"),
    category: str = Query(..., description="직무 카테고리 (예: 프론트엔드 개발자)"),
    db: Session = Depends(get_db)
):
    """
    사용자의 이력 정보와 선택한 직무를 바탕으로 LLM 기반 갭차이 분석을 수행합니다.
    분석 결과는 자연어 설명과 부족 역량 Top 5 리스트로 구성됩니다.
    """
    try:
        result = perform_gap_analysis(user_id, category, engine=db)

        # 1. 프론트에 보여줄 자연어 결과
        gap_result = result["gap_result"]

        # 2. 내부 To-Do 시스템으로 보낼 Top 5 스킬
        top_skills = result["top_skills"]
        # 예시: 추후 비동기로 보내거나 DB에 저장
        # send_to_todo(user_id, top_skills)

        return {
            "gap_result": gap_result,      # 프론트에 출력할 자연어
            "top_skills": top_skills       # 프론트가 투두 리스트로 활용 가능
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")