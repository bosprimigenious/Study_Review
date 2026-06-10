"""Intent classification for StudyReviewOrchestrator."""

from __future__ import annotations

INTENTS = [
    "init_course",
    "analyze_exam",
    "generate_questions",
    "make_plan",
    "start_review",
    "grade_answer",
    "log_mistake",
    "due_review",
]

INTENT_KEYWORDS = [
    ("make_plan", ["今晚怎么", "不挂", "救火", "速成", "来不及", "只剩", "计划", "规划", "安排"]),
    ("analyze_exam", ["试卷", "往年题", "样题", "真题", "分析重点", "考频", "高频", "题型"]),
    ("generate_questions", ["出题", "生成题", "变式", "模拟题", "题目", "刷题", "练习"]),
    ("start_review", ["开始复习", "抽查", "抽背", "考我", "问我", "答题", "摸底", "开始刷"]),
    ("due_review", ["今天复习什么", "该复习什么", "复查", "错题", "due", "到期"]),
    ("init_course", ["初始化", "开始", "新建", "创建", "注册课程"]),
]


def classify_intent(user_message: str) -> str:
    """Simple keyword-based intent classifier. Returns intent name."""
    message = user_message.lower()
    for intent, keywords in INTENT_KEYWORDS:
        for keyword in keywords:
            if keyword in message:
                return intent
    return "start_review"
