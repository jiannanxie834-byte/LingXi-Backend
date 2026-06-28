from pydantic import BaseModel


class CourseProfile(BaseModel):
    course_id: str
    course_name: str
    course_display_name: str
    course_full_name: str
    course_positioning: str
    default_scope_message: str
    chapters: list[dict]
    resource_types: list[str]
    multimodal_modes: list[str]
