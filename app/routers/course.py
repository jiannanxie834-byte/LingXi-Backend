from fastapi import APIRouter, Query

from app.services.data_services import (
    deep_learning_course_map_service,
    video_catalog_service,
)


router = APIRouter(prefix="/course", tags=["深度学习课程"])


@router.get("/deep-learning/map")
async def get_deep_learning_map():
    return {
        "code": 200,
        "message": "ok",
        "data": deep_learning_course_map_service.course_map_payload(),
    }


@router.get("/deep-learning/units")
async def get_deep_learning_units():
    return {
        "code": 200,
        "message": "ok",
        "data": deep_learning_course_map_service.list_units(),
    }


@router.get("/deep-learning/match")
async def match_deep_learning_topic(
    topic: str = Query("", description="课程主题或知识点"),
    message: str = Query("", description="学生原始输入"),
):
    return {
        "code": 200,
        "message": "ok",
        "data": deep_learning_course_map_service.match_deep_learning_topic(topic, message),
    }


@router.get("/deep-learning/video/catalog")
async def get_video_catalog():
    return {
        "code": 200,
        "message": "ok",
        "data": video_catalog_service.list_video_catalog(),
    }


@router.get("/deep-learning/video/recommendations")
async def get_video_recommendations(
    unit_id: str = "",
    topic: str = "",
    limit: int = 6,
):
    return {
        "code": 200,
        "message": "ok",
        "data": video_catalog_service.search_videos(unit_id=unit_id, topic=topic, limit=limit),
    }
