from fastapi import APIRouter

from app.services.data_services import video_catalog_service


router = APIRouter(prefix="/video", tags=["公开视频推荐"])


@router.get("/catalog")
async def list_video_catalog():
    return {"code": 200, "message": "ok", "data": video_catalog_service.list_video_catalog()}


@router.get("/recommendations")
async def get_video_recommendations(unit_id: str = "", topic: str = "", limit: int = 6):
    return {
        "code": 200,
        "message": "ok",
        "data": video_catalog_service.search_videos(unit_id=unit_id, topic=topic, limit=limit),
    }
