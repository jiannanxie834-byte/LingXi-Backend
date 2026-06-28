from app.services.course_registry.course_profile import CourseProfile


DEFAULT_COURSE_ID = "data_structures_algorithms"

DSA_CHAPTERS = [
    {"chapter_id": "chapter_01_complexity", "chapter_no": 1, "title": "算法导论与复杂度分析"},
    {"chapter_id": "chapter_02_linear_structures", "chapter_no": 2, "title": "数组、链表、栈与队列"},
    {"chapter_id": "chapter_03_recursion_divide_backtracking", "chapter_no": 3, "title": "递归、分治与回溯"},
    {"chapter_id": "chapter_04_sorting_searching", "chapter_no": 4, "title": "排序与查找算法"},
    {"chapter_id": "chapter_05_hash_heap_priority_queue", "chapter_no": 5, "title": "哈希表、堆与优先队列"},
    {"chapter_id": "chapter_06_trees", "chapter_no": 6, "title": "树、二叉树与搜索树"},
    {"chapter_id": "chapter_07_graph_traversal", "chapter_no": 7, "title": "图的表示、BFS 与 DFS"},
    {"chapter_id": "chapter_08_shortest_path_mst", "chapter_no": 8, "title": "最短路径与最小生成树"},
    {"chapter_id": "chapter_09_greedy", "chapter_no": 9, "title": "贪心算法"},
    {"chapter_id": "chapter_10_dynamic_programming", "chapter_no": 10, "title": "动态规划"},
    {"chapter_id": "chapter_11_string_algorithms", "chapter_no": 11, "title": "字符串算法与匹配"},
    {"chapter_id": "chapter_12_algorithm_project", "chapter_no": 12, "title": "综合项目：算法可视化与刷题训练系统"},
]

DSA_RESOURCE_TYPES = [
    "course_note",
    "mind_map",
    "exercise_set",
    "code_lab",
    "visual_animation",
    "comparison_table",
    "debug_task",
    "project_brief",
    "learning_path",
    "remediation_report",
    "video_recommendation",
    "personalized_guide",
    "ppt_outline",
]

COURSE_PROFILES = {
    "data_structures_algorithms": CourseProfile(
        course_id="data_structures_algorithms",
        course_name="数据结构与算法",
        course_display_name="《数据结构与算法》",
        course_full_name="《数据结构与算法：可视化理解与代码实践》",
        course_positioning=(
            "面向计算机科学与技术、软件工程、人工智能、电子信息等专业本科低年级至中年级学生的"
            "专业基础核心课程，覆盖数据结构、算法设计思想、复杂度分析、代码实现、题目训练和可视化理解。"
        ),
        default_scope_message="本系统聚焦《数据结构与算法》课程，暂未纳入课程图谱的主题不会进入资源生成主链路。",
        chapters=DSA_CHAPTERS,
        resource_types=DSA_RESOURCE_TYPES,
        multimodal_modes=[
            "文本讲解",
            "结构化思维导图",
            "练习题集",
            "代码实验",
            "算法可视化动画规格",
            "项目任务书",
        ],
    ),
}


def get_course_profile(course_id: str = DEFAULT_COURSE_ID) -> CourseProfile:
    return COURSE_PROFILES.get(course_id) or COURSE_PROFILES[DEFAULT_COURSE_ID]


def get_default_course_profile() -> CourseProfile:
    return get_course_profile(DEFAULT_COURSE_ID)
