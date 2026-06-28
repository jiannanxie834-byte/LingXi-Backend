from app.agents.agent_result_dto import AgentResultDTO


def _spec(animation_type: str, title: str):
    return {
        "animation_type": animation_type,
        "title": title,
        "steps": [
            {"step": 1, "label": "初始化", "explanation": "准备输入数据、指针、辅助结构或状态表。"},
            {"step": 2, "label": "核心操作", "explanation": "逐步高亮算法的比较、移动、入栈、出队、松弛或状态转移过程。"},
            {"step": 3, "label": "结果复盘", "explanation": "展示输出结果、复杂度观察和常见错误位置。"},
        ],
        "placeholder": True,
        "note": "本阶段只输出算法动画规格占位，不实现正式动画细节。",
    }


def run(unit_id: str = "", topic: str = "") -> AgentResultDTO:
    text = f"{unit_id} {topic}".lower()
    if "sort" in text or "排序" in text:
        spec = _spec("sort_animation", topic or "排序算法")
    elif "binary" in text or "二分" in text:
        spec = _spec("binary_search_animation", topic or "二分查找")
    elif "recursion" in text or "递归" in text:
        spec = _spec("recursion_call_stack", topic or "递归调用栈")
    elif "backtracking" in text or "回溯" in text:
        spec = _spec("backtracking_tree", topic or "回溯搜索树")
    elif "tree" in text or "树" in text:
        spec = _spec("tree_traversal_animation", topic or "树遍历")
    elif "dijkstra" in text or "最短路径" in text:
        spec = _spec("dijkstra_relaxation_animation", topic or "Dijkstra 松弛过程")
    elif "union" in text or "并查集" in text or "mst" in text:
        spec = _spec("mst_union_find_animation", topic or "并查集与最小生成树")
    elif "dp" in text or "动态规划" in text:
        spec = _spec("dp_table_animation", topic or "动态规划表格")
    elif "kmp" in text or "字符串" in text:
        spec = _spec("kmp_prefix_animation", topic or "KMP 前缀函数")
    elif "heap" in text or "堆" in text:
        spec = _spec("heap_operation_animation", topic or "堆操作")
    else:
        spec = _spec("bfs_dfs_graph_animation", topic or "图搜索算法")
    return AgentResultDTO(
        agent_name="InteractiveAnimationAgent",
        input_summary=topic or unit_id,
        output={"type": "interactive_animation", "format": "animation_spec", "spec": spec},
        evidence_refs=[unit_id] if unit_id else [],
        quality_score=0.5,
    )
