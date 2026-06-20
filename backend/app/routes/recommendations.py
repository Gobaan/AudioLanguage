from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.recommendations import MAX_RECOMMENDED_PHRASE_LENGTH
from app.runtime import recommended_phrase_store
from app.validation.location import client_ip_from_request, location_flag_from_country_code, location_flag_from_ip

router = APIRouter()


class RecommendedPhraseRequest(BaseModel):
    phrase: str = Field(min_length=1, max_length=MAX_RECOMMENDED_PHRASE_LENGTH)


@router.post("/api/recommended-phrases")
def recommend_phrase(request: RecommendedPhraseRequest, http_request: Request):
    client_ip = client_ip_from_request(http_request)
    try:
        return recommended_phrase_store.add(
            request.phrase,
            client_ip=client_ip,
            location_flag=location_flag_from_country_code(http_request) or location_flag_from_ip(client_ip),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/api/admin/recommended-phrases")
def recommended_phrase_summary(index: int = Query(default=0, ge=0)):
    return recommended_phrase_store.summary(index)
