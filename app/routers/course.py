from fastapi import APIRouter, Query

from app.services.data_services import (
    dsa_framework_service,
    dsa_course_map_service,
    video_catalog_service,
)


router = APIRouter(prefix="/course", tags=["数据结构与算法课程"])


@router.get("/data-structures-algorithms/map")
@router.get("/deep-learning/map")
async def get_course_map():
    return {
        "code": 200,
        "message": "ok",
        "data": dsa_course_map_service.course_map_payload(),
    }


@router.get("/data-structures-algorithms/framework")
async def get_dsa_framework():
    return {
        "code": 200,
        "message": "ok",
        "data": dsa_framework_service.load_framework_payload(),
    }


@router.get("/data-structures-algorithms/framework/validate")
async def validate_dsa_framework():
    return {
        "code": 200,
        "message": "ok",
        "data": dsa_framework_service.validate_framework_structure(),
    }


@router.get("/data-structures-algorithms/units")
@router.get("/deep-learning/units")
async def get_course_units():
    return {
        "code": 200,
        "message": "ok",
        "data": dsa_course_map_service.list_units(),
    }


@router.get("/data-structures-algorithms/match")
@router.get("/deep-learning/match")
async def match_course_topic(
    topic: str = Query("", description="课程主题或知识点"),
    message: str = Query("", description="学生原始输入"),
):
    return {
        "code": 200,
        "message": "ok",
        "data": dsa_course_map_service.match_dsa_topic(topic, message),
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
