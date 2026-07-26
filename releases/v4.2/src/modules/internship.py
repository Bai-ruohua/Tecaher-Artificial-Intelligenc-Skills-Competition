# -*- coding: utf-8 -*-
"""
顶岗实习家校沟通模块
- 实习周报模板生成
- 家长沟通话术生成
- 实习表现告知函
- 批量生成沟通文案
"""
import json
import os
import sys

_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _src not in sys.path:
    sys.path.insert(0, _src)

from deepseek_client import deepseek

# 沟通场景模板
SCENARIOS = {
    "daily": {
        "name": "日常实习反馈",
        "system": "你是一位高职实习指导教师，擅长与学生家长沟通实习情况。语气亲切、专业。",
        "user": "请为以下学生生成一份给家长的日常实习反馈（300字以内）：\n学生：{student_name}\n实习岗位：{position}\n实习单位：{company}\n本周表现：{performance}",
    },
    "warning": {
        "name": "风险预警通知",
        "system": "你是一位高职实习指导教师，需要向家长通报学生实习异常情况。语气严肃但关怀，给出改进建议。",
        "user": "请生成一份实习预警告知函（300字以内）：\n学生：{student_name}\n实习岗位：{position}\n异常情况：{issue}",
    },
    "evaluation": {
        "name": "实习鉴定告知",
        "system": "你是一位高职实习指导教师，向家长告知学生实习鉴定结果。语气正式、鼓励。",
        "user": "请生成实习鉴定告知函（200字以内）：\n学生：{student_name}\n实习岗位：{position}\n实习单位：{company}\n实习评价：{evaluation}\n综合评分：{score}/100",
    },
}


def generate_communication(student_name, position, company, scenario="daily", performance="", issue="", evaluation="", score=80):
    """生成沟通文案"""
    template = SCENARIOS.get(scenario, SCENARIOS["daily"])
    user_msg = template["user"].format(
        student_name=student_name,
        position=position,
        company=company,
        performance=performance or "按时完成实习任务，态度积极",
        issue=issue or "",
        evaluation=evaluation or "表现良好",
        score=score,
    )
    try:
        result = deepseek.chat(template["system"], user_msg)
        return {"success": True, "content": result, "scenario": template["name"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_generate(student_list, scenario="daily"):
    """批量生成沟通文案"""
    results = []
    for student in student_list:
        r = generate_communication(
            student_name=student.get("name", ""),
            position=student.get("position", ""),
            company=student.get("company", ""),
            scenario=scenario,
            performance=student.get("performance", ""),
            issue=student.get("issue", ""),
            evaluation=student.get("evaluation", ""),
            score=student.get("score", 80),
        )
        results.append({**r, "student_name": student.get("name", "")})
    return results


# 示例学生数据用于演示
DEMO_STUDENTS = [
    {"name": "张明轩", "position": "数据标注员", "company": "四川文德数慧科技有限公司", "performance": "本周完成标注量1200条，准确率98.5%，团队协作良好"},
    {"name": "李思琪", "position": "Python开发实习生", "company": "成都智云科技有限公司", "performance": "完成API接口开发任务，代码质量通过评审"},
    {"name": "王浩然", "position": "数据分析助理", "company": "宜宾大数据中心", "performance": "参与数据分析项目，独立完成数据清洗工作"},
    {"name": "陈雅文", "position": "前端开发实习生", "company": "成都创想科技有限公司", "performance": "完成3个页面开发，响应式适配达标"},
    {"name": "刘子轩", "position": "测试工程师", "company": "四川华迪信息技术有限公司", "performance": "编写测试用例50个，发现Bug12个"},
]
