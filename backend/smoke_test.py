# -*- coding: utf-8 -*-
"""后端接口冒烟测试：CRUD + 入参校验 + 错误处理 + 持久化。

用法（需后端已启动）：
    venv\\Scripts\\python smoke_test.py [base_url]

默认 base_url = http://127.0.0.1:8000，可指定其他端口/代理地址。
脚本只创建/删除名称带「【冒烟测试】」前缀的数据，不会碰其他数据。
"""
import json
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = BASE.rstrip("/") + "/api"

MARKER = "【冒烟测试】"

# 测试夹具直接写 SQLite（仅用于构造 HTTP 层无法创建的受控输入，
# 如带全文的文献、带建议的分析记录；数据均为本脚本创建、以 MARKER 标识、用后清理）
DB_PATH = Path(__file__).resolve().parent / "research.db"


def db_execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def call_upload(path, filename, content_type, data):
    """multipart/form-data 上传（附件/文件类接口用）。"""
    boundary = "----smoketestboundary987"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(API + path, method="POST", data=body)
    req.add_header(
        "Content-Type", f"multipart/form-data; boundary={boundary}"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None


def has_marker(project):
    return project.get("name", "").startswith(MARKER)

passed = 0
failed = 0


def call(method, path, body=None, raw_body=None):
    """发起请求，返回 (状态码, 解析后的 JSON 或 None)。"""
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Content-Type", "application/json")
    data = None
    if raw_body is not None:
        data = raw_body
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
    try:
        with urllib.request.urlopen(req, data) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, json.loads(raw) if raw else None


def check(name, cond, extra=""):
    global passed, failed
    if cond:
        passed += 1
        print(f"[PASS] {name}")
    else:
        failed += 1
        print(f"[FAIL] {name} {extra}")


def detail_contains(body, text):
    return text in json.dumps(body, ensure_ascii=False)


print(f"===== ResearchPilot 后端冒烟测试（{API}）=====\n")

# ── 0. 清理上次测试残留（只删本脚本创建的数据） ───────────────────────
code, body = call("GET", "/projects")
if body:
    for p in body:
        if has_marker(p):
            call("DELETE", f"/projects/{p['id']}")

# ── 1. 健康检查 ────────────────────────────────────────────────────
code, body = call("GET", "/health")
check("1.1 健康检查", code == 200 and body["status"] == "ok")

# ── 2. 创建项目 ────────────────────────────────────────────────────
code, proj = call("POST", "/projects", {
    "name": MARKER + "毕业论文",
    "goal": "2026年12月底前完成毕业论文初稿",
    "deadline": "2026-12-31",
    "weeklyHours": 15,
})
check("2.1 创建项目（合法）", code == 201 and proj["risk"] == "none" and proj["progress"] == 0, f"code={code}")
project_id = proj["id"]

code, body = call("POST", "/projects", {"name": "   ", "goal": "x", "deadline": "2026-12-31", "weeklyHours": 15})
check("2.2 空项目名称 → 422 中文提示", code == 422 and detail_contains(body, "项目名称不能为空"), f"code={code}")

code, body = call("POST", "/projects", {"name": "x", "goal": "x", "deadline": "2026-12-31", "weeklyHours": 0})
check("2.3 weeklyHours=0 → 422", code == 422 and detail_contains(body, "每周可用小时数必须大于 0"), f"code={code}")

code, body = call("POST", "/projects", {"name": "x", "goal": "x", "deadline": "2020-01-01", "weeklyHours": 10})
check("2.4 过去截止日期 → 422", code == 422 and detail_contains(body, "截止日期不能早于今天"), f"code={code}")

code, body = call("POST", "/projects", {"name": "x", "goal": "x"})  # 缺 deadline / weeklyHours
check("2.5 缺少必填字段 → 422", code == 422, f"code={code}")

# 非 UTF-8 请求体（Windows 终端 curl 中文的 GBK 编码场景）：不得 500，且提示可读
code, body = call("POST", "/projects", raw_body='{"name": "测试", "goal": "x"}'.encode("gbk"))
check("2.6 GBK 编码请求体 → 400/422 而非 500", code in (400, 422) and detail_contains(body, "UTF-8"), f"code={code} body={body}")

# ── 3. 项目查询 / 更新 / 删除 ───────────────────────────────────────
code, body = call("GET", "/projects")
check("3.1 项目列表包含新项目", code == 200 and any(p["id"] == project_id for p in body))

code, body = call("PUT", f"/projects/{project_id}", {"weeklyHours": 20, "name": MARKER + "毕业论文（改）"})
check("3.2 更新项目", code == 200 and body["weeklyHours"] == 20 and body["name"] == MARKER + "毕业论文（改）")

code, body = call("GET", "/projects/99999")
check("3.3 不存在的项目 → 404", code == 404 and detail_contains(body, "项目不存在"))

# ── 4. 创建任务 ────────────────────────────────────────────────────
code, task = call("POST", "/tasks", {
    "projectId": project_id,
    "title": "完成文献综述初稿",
    "description": "阅读 30 篇文献并整理",
    "priority": "high",
    "plannedStartDate": "2026-10-12",
    "plannedEndDate": "2026-10-30",
    "estimatedHours": 20,
})
check("4.1 创建任务（合法）", code == 201 and task["status"] == "todo", f"code={code}")
task_id = task["id"]

code, body = call("POST", "/tasks", {"projectId": project_id, "title": "x", "priority": "urgent"})
check("4.2 非法优先级 → 422", code == 422 and detail_contains(body, "优先级"), f"code={code}")

code, body = call("POST", "/tasks", {
    "projectId": project_id, "title": "x",
    "plannedStartDate": "2026-11-01", "plannedEndDate": "2026-10-01",
})
check("4.3 计划日期倒挂 → 422", code == 422 and detail_contains(body, "计划截止日期不能早于计划开始日期"), f"code={code}")

code, body = call("POST", "/tasks", {"projectId": project_id, "title": "x", "parentId": 99999})
check("4.4 父任务不存在 → 404", code == 404 and detail_contains(body, "父任务不存在"), f"code={code}")

code, body = call("POST", "/tasks", {"projectId": 99999, "title": "x"})
check("4.5 挂到不存在的项目 → 404", code == 404 and detail_contains(body, "项目不存在"), f"code={code}")

code, body = call("POST", "/tasks", {"projectId": project_id, "title": "   "})
check("4.6 空任务标题 → 422", code == 422 and detail_contains(body, "任务标题不能为空"), f"code={code}")

# ── 5. 任务状态流转 ────────────────────────────────────────────────
code, task = call("PUT", f"/tasks/{task_id}", {"status": "doing"})
check("5.1 → 进行中", code == 200 and task["status"] == "doing")

code, task = call("PUT", f"/tasks/{task_id}", {"status": "done"})
check("5.2 → 已完成（进度自动 100）", code == 200 and task["status"] == "done" and task["progress"] == 100)

code, body = call("PUT", f"/tasks/{task_id}", {"status": "unknown"})
check("5.3 非法状态 → 422", code == 422 and detail_contains(body, "任务状态"), f"code={code}")

code, task = call("PUT", f"/tasks/{task_id}", {"progress": 40})
check("5.4 已完成任务回退进度 → 自动回到进行中", code == 200 and task["status"] == "doing" and task["progress"] == 40)

code, task = call("PUT", f"/tasks/{task_id}", {"progress": 100})
check("5.5 进度拉满 → 自动完成", code == 200 and task["status"] == "done" and task["progress"] == 100)

code, body = call("PUT", f"/tasks/{task_id}", {"progress": 150})
check("5.6 进度 150 → 422", code == 422 and detail_contains(body, "进度必须在 0 到 100 之间"), f"code={code}")

code, body = call("PUT", f"/tasks/{task_id}", {"plannedStartDate": "2026-11-01"})
check("5.7 更新后日期倒挂 → 400", code == 400 and detail_contains(body, "计划截止日期不能早于计划开始日期"), f"code={code} body={body}")

# ── 6. 进度记录 ────────────────────────────────────────────────────
code, task = call("PUT", f"/tasks/{task_id}", {"plannedStartDate": "2026-10-12", "status": "doing"})
code, body = call("POST", f"/tasks/{task_id}/progress", {"progress": 60, "hoursSpent": 3.5, "note": "整理目录结构"})
check("6.1 新增进度记录", code == 200 and body["record"]["progress"] == 60 and body["task"]["progress"] == 60)

code, body = call("POST", f"/tasks/{task_id}/progress", {"progress": 150})
check("6.2 进度记录 150 → 422", code == 422, f"code={code}")

code, body = call("GET", f"/tasks/{task_id}/progress")
check("6.3 进度记录列表（升序）", code == 200 and len(body) == 1 and body[0]["hoursSpent"] == 3.5)

code, body = call("POST", "/tasks/99999/progress", {"progress": 50})
check("6.4 不存在的任务记进度 → 404", code == 404 and detail_contains(body, "任务不存在"))

# ── 7. 项目详情 / 首页聚合 ──────────────────────────────────────────
code, body = call("GET", f"/projects/{project_id}")
check("7.1 项目详情（含任务与风险字段）", code == 200 and len(body["tasks"]) == 1
      and body["project"]["tasksTotal"] == 1 and body["project"]["progress"] == 60)

code, body = call("GET", "/home")
check("7.2 首页聚合", code == 200 and body["stats"]["activeProjects"] >= 1
      and body["stats"]["todoTasks"] >= 1
      and body["distribution"][1]["value"] >= 1  # 进行中 ≥1 个
      and len(body["trend"]) == 7)

# ── 8. 风险引擎（构造逾期任务） ─────────────────────────────────────
code, body = call("POST", "/tasks", {
    "projectId": project_id,
    "title": "已逾期的任务",
    "plannedEndDate": "2026-10-01",  # 已过去
})
overdue_id = body["id"]
code, body = call("GET", f"/projects/{project_id}")
overdue_task = next(t for t in body["tasks"] if t["id"] == overdue_id)
check("8.1 逾期任务 → 高风险", overdue_task["risk"] == "high" and "已逾期" in overdue_task["riskReason"],
      overdue_task.get("riskReason", ""))
check("8.2 项目级风险 → 高风险", body["project"]["risk"] == "high")
code, body = call("GET", "/home")
check("8.3 首页风险提醒", body["stats"]["riskTaskCount"] >= 1 and len(body["riskTasks"]) >= 1)

# ── 9. 删除（级联） ─────────────────────────────────────────────────
code, body = call("DELETE", f"/tasks/{task_id}")
check("9.1 删除任务", code == 204)

code, body = call("DELETE", f"/projects/{project_id}")
check("9.2 删除项目（级联）", code == 204)
code, body = call("GET", f"/projects/{project_id}")
check("9.3 删除后查询 → 404", code == 404)

code, body = call("GET", "/home")
check("9.4 删除后列表不再含测试项目", code == 200 and not any(has_marker(p) for p in body["projects"]))

# ═══════════════════════ v2：科研工作台 ═══════════════════════
# 10~17：研究问题 / 文献卡片 / 实验 / 运行记录 / AI 分析 / 决策闭环 / 实验风险
# AI 依赖项（卡片抽取、分析生成）在无 Key 的演示模式与报错路径下测试；
# 需要 AI 建议才能走的"转任务"闭环用 SQLite 夹具构造受控输入。

code, proj = call("POST", "/projects", {
    "name": MARKER + "v2科研工作台",
    "goal": "验证研究问题-证据-实验-分析-任务闭环",
    "deadline": "2027-06-30",
    "weeklyHours": 10,
})
check("10.1 创建 v2 测试项目", code == 201, f"code={code}")
v2_project_id = proj["id"]

# ── 11. 研究问题 ────────────────────────────────────────────────────
code, q = call("POST", f"/projects/{v2_project_id}/questions", {
    "content": "方法A是否在数据集X上优于方法B？",
})
check("11.1 创建研究问题", code == 201 and q["status"] == "open"
      and q["evidenceSupport"] == 0 and q["experimentsCount"] == 0, f"code={code}")
question_id = q["id"]

code, body = call("POST", f"/projects/{v2_project_id}/questions", {"content": "   "})
check("11.2 空问题 → 422", code == 422 and detail_contains(body, "研究问题不能为空"), f"code={code}")

code, q = call("PUT", f"/questions/{question_id}", {"status": "answered", "answerSummary": "初步结论：A 略优"})
check("11.3 更新问题状态与解答摘要", code == 200 and q["status"] == "answered" and "A 略优" in q["answerSummary"], f"code={code}")

code, body = call("GET", f"/projects/{v2_project_id}/questions")
check("11.4 问题列表", code == 200 and len(body) == 1 and body[0]["id"] == question_id, f"code={code}")

code, body = call("GET", "/questions/99999")
check("11.5 不存在的问题 → 404", code == 404 and detail_contains(body, "研究问题不存在"), f"code={code}")

# ── 12. 文献卡片（手工 + AI 抽取演示模式 + 对比） ─────────────────────
code, card = call("POST", f"/projects/{v2_project_id}/cards", {
    "title": "手工卡片：方法A综述",
    "method": "对比实验",
    "metrics": "Accuracy; F1",
    "keyResults": "方法A平均提升2个百分点",
    "questionId": question_id,
    "evidenceType": "support",
})
check("12.1 手工创建卡片", code == 201 and card["source"] == "manual" and card["questionId"] == question_id, f"code={code}")
card1_id = card["id"]

code, card2 = call("POST", f"/projects/{v2_project_id}/cards", {
    "title": "手工卡片：方法B论文",
    "evidenceType": "against",
    "questionId": question_id,
})
check("12.2 第二张卡片（字段可留空）", code == 201 and card2["evidenceType"] == "against", f"code={code}")
card2_id = card2["id"]

code, body = call("POST", f"/projects/{v2_project_id}/cards", {"title": "x", "evidenceType": "wrong"})
check("12.3 非法证据立场 → 422", code == 422 and detail_contains(body, "证据立场"), f"code={code}")

code, card = call("PUT", f"/cards/{card1_id}", {"keyResults": "方法A平均提升2个百分点（人工修订）"})
check("12.4 修改卡片 → source 置 manual", code == 200 and card["source"] == "manual"
      and "人工修订" in card["keyResults"], f"code={code}")

code, body = call("GET", f"/projects/{v2_project_id}/questions")
check("12.5 问题证据计数", code == 200 and body[0]["evidenceSupport"] == 1 and body[0]["evidenceAgainst"] == 1, f"code={code} body={body}")

code, body = call("GET", f"/projects/{v2_project_id}/cards/compare", )
check("12.6 对比缺 card_ids → 422", code == 422, f"code={code}")
code, body = call("GET", f"/projects/{v2_project_id}/cards/compare?card_ids={card1_id},{card2_id}")
check("12.7 两卡片对比（按传入顺序）", code == 200 and len(body["cards"]) == 2
      and body["cards"][0]["id"] == card1_id, f"code={code}")

# AI 抽取：夹具注入一篇带全文的文献，无 Key 时演示模式返回空模板（不伪造）
doc_id = db_execute(
    "INSERT INTO document (project_id, title, file_name, full_text, chunk_count, created_at) "
    "VALUES (?, ?, ?, ?, 1, datetime('now'))",
    (v2_project_id, MARKER + "夹具文献", "fixture.pdf", "This is a research paper text.", ),
)
code, body = call("POST", f"/documents/{doc_id}/card")
check("12.8 AI 抽取卡片（演示模式空模板）", code == 200 and body["card"]["source"] in ("demo", "deepseek")
      and "warning" in body, f"code={code} body={body}")
extracted_card_id = body["card"]["id"] if code == 200 else None

if extracted_card_id:
    code, body = call("POST", f"/documents/{doc_id}/card")
    check("12.9 重复抽取 → 400", code == 400 and detail_contains(body, "已有研究卡片"), f"code={code}")

# ── 13. 实验管理 ────────────────────────────────────────────────────
code, exp = call("POST", f"/projects/{v2_project_id}/experiments", {
    "title": MARKER + "方法A vs 方法B 对比实验",
    "objective": "验证方法A是否优于方法B",
    "hypothesis": "方法A的精度更高",
    "questionId": question_id,
    "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True},
                {"name": "F1", "unit": "", "higherIsBetter": True}],
    "status": "running",
})
check("13.1 创建实验（含指标定义）", code == 201 and exp["status"] == "running"
      and len(exp["metrics"]) == 2, f"code={code}")
experiment_id = exp["id"]

code, body = call("POST", f"/projects/{v2_project_id}/experiments", {"title": "x", "objective": "   "})
check("13.2 空实验目的 → 422", code == 422 and detail_contains(body, "实验目的不能为空"), f"code={code}")

code, body = call("GET", f"/projects/{v2_project_id}/questions")
check("13.3 问题关联实验计数", code == 200 and body[0]["experimentsCount"] == 1, f"code={code}")

# ── 14. 运行记录 + 附件 + 对比 ──────────────────────────────────────
code, run1 = call("POST", f"/experiments/{experiment_id}/runs", {
    "config": {"lr": 0.001, "epochs": 50},
    "results": {"Accuracy": 82.5, "F1": 0.81},
    "notes": "第一次运行，方法A",
})
check("14.1 新增运行记录 run#1", code == 201 and run1["runNo"] == 1 and run1["results"]["Accuracy"] == 82.5, f"code={code}")

code, run2 = call("POST", f"/experiments/{experiment_id}/runs", {
    "config": {"lr": 0.0005, "epochs": 50},
    "results": {"Accuracy": 87.3, "F1": 0.86},
})
check("14.2 新增运行记录 run#2（自动编号）", code == 201 and run2["runNo"] == 2, f"code={code}")

code, body = call("POST", f"/experiments/{experiment_id}/runs", {"results": "not-a-dict"})
check("14.3 结果非对象 → 422", code == 422, f"code={code}")

# 附件上传（PNG 魔数即可通过校验，后端只存字节）
fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
code, body = call_upload(f"/runs/{run1['id']}/attachments", "result.png", "image/png", fake_png)
check("14.4 上传附件图片", code == 200 and len(body["attachments"]) == 1, f"code={code}")

code, body = call_upload(f"/runs/{run1['id']}/attachments", "bad.txt", "text/plain", b"hello")
check("14.5 非图片附件 → 400", code == 400 and detail_contains(body, "PNG/JPG"), f"code={code}")

code, body = call("GET", f"/experiments/{experiment_id}/compare")
check("14.6 同实验对比（指标对齐）", code == 200 and body["metricNames"] == ["Accuracy", "F1"]
      and len(body["rows"]) == 2 and body["rows"][1]["values"]["Accuracy"] == 87.3, f"code={code}")

code, body = call("GET", f"/projects/{v2_project_id}/metrics")
check("14.7 跨实验指标总览", code == 200 and len(body["metrics"]) == 2
      and body["metrics"][0]["points"][1]["value"] == 87.3, f"code={code}")

code, body = call("PUT", f"/runs/{run1['id']}", {"notes": "第一次运行（已修订备注）"})
check("14.8 修改运行记录", code == 200 and "已修订备注" in body["notes"], f"code={code}")

# ── 15. AI 分析（无 run → 400；无 Key → 400；手工笔记；历史） ─────────
code, exp2 = call("POST", f"/projects/{v2_project_id}/experiments", {
    "title": MARKER + "空实验", "objective": "没有运行记录的实验", "status": "draft",
})
empty_experiment_id = exp2["id"]
code, body = call("POST", f"/experiments/{empty_experiment_id}/analysis")
check("15.1 无运行记录生成分析 → 400", code == 400 and detail_contains(body, "运行记录"), f"code={code}")

code, body = call("POST", f"/experiments/{experiment_id}/analysis")
# 无 Key → 400 提示手工笔记；有 Key 时可能 200/502（真实 AI 调用），按环境处理
if code == 400 and "DeepSeek" in json.dumps(body, ensure_ascii=False):
    check("15.2 无 Key 生成分析 → 400 明确提示", True, f"code={code}")
else:
    print(f"[SKIP] 15.2 已配置 API Key 或网络异常（HTTP {code}），跳过无 Key 断言")

code, note = call("POST", f"/experiments/{experiment_id}/analysis/notes", {
    "content": "手工分析：第二次运行精度提升明显，可能与学习率有关。",
})
check("15.3 手工分析笔记", code == 201 and note["source"] == "manual" and len(note["runIds"]) == 2, f"code={code}")
note_id = note["id"]

code, body = call("GET", f"/experiments/{experiment_id}/analyses")
check("15.4 分析历史", code == 200 and any(a["id"] == note_id for a in body), f"code={code}")

# ── 16. 决策闭环：建议转任务（夹具注入带建议的分析记录） ─────────────
suggestions = [{"type": "new_task", "content": MARKER + "消融实验：冻结主干网络重训",
                "reason": "定位精度提升来源", "converted": False}]
analysis_id = db_execute(
    "INSERT INTO experiment_analysis (project_id, experiment_id, question_id, run_ids_json, "
    "content, suggestions_json, source, created_at) VALUES (?, ?, ?, ?, ?, ?, 'deepseek', datetime('now'))",
    (v2_project_id, experiment_id, question_id, json.dumps([run1["id"], run2["id"]]),
     "夹具分析内容", json.dumps(suggestions, ensure_ascii=False)),
)
code, task = call("POST", f"/analyses/{analysis_id}/suggestions/0/to-task")
check("16.1 建议转任务（带来源标记）", code == 201 and task["sourceType"] == "experiment_analysis"
      and task["sourceId"] == analysis_id and MARKER in task["title"], f"code={code} task={task}")
converted_task_id = task["id"] if code == 201 else None

code, body = call("POST", f"/analyses/{analysis_id}/suggestions/0/to-task")
check("16.2 重复转换 → 400（防重复）", code == 400 and detail_contains(body, "已转换"), f"code={code}")

code, body = call("POST", f"/analyses/{analysis_id}/suggestions/5/to-task")
check("16.3 不存在的建议 → 404", code == 404, f"code={code}")

code, exp3 = call("POST", f"/analyses/{analysis_id}/suggestions/0/to-experiment")
check("16.4 重复转换（转实验）→ 400", code == 400, f"code={code}")

# ── 17. 实验科研风险（停滞/失败） ────────────────────────────────────
code, failed_exp = call("POST", f"/projects/{v2_project_id}/experiments", {
    "title": MARKER + "失败的实验", "objective": "已失败的实验", "status": "failed",
})
check("17.1 创建失败状态实验", code == 201, f"code={code}")

code, body = call("GET", f"/projects/{v2_project_id}")
risks = body.get("experimentRisks") or []
check("17.2 项目详情含实验科研风险（失败待复盘）", code == 200
      and any("失败" in r["reason"] for r in risks), f"code={code} risks={risks}")

# 停滞风险：把运行中实验及其运行记录的时间改到 10 天前（夹具注入历史时间）
db_execute(
    "UPDATE experiment SET created_at = datetime('now', '-10 days') WHERE id = ?",
    (experiment_id,),
)
db_execute(
    "UPDATE experiment_run SET created_at = datetime('now', '-10 days') WHERE experiment_id = ?",
    (experiment_id,),
)
code, body = call("GET", f"/projects/{v2_project_id}")
risks = body.get("experimentRisks") or []
check("17.3 实验停滞 → 中风险提醒", code == 200
      and any(r["experimentId"] == experiment_id and "停滞" in r["reason"] for r in risks),
      f"code={code} risks={risks}")

# ── 18. v2 清理（级联） ─────────────────────────────────────────────
code, body = call("DELETE", f"/projects/{v2_project_id}")
check("18.1 删除 v2 项目（级联清理新表数据）", code == 204)
code, body = call("GET", f"/projects/{v2_project_id}/questions")
check("18.2 删除后问题列表 → 404", code == 404)
code, body = call("GET", f"/projects/{v2_project_id}/experiments")
check("18.3 删除后实验列表 → 404", code == 404)
conn = sqlite3.connect(DB_PATH)
leftover = conn.execute(
    "SELECT COUNT(*) FROM literature_card WHERE project_id = ?", (v2_project_id,)
).fetchone()[0]
conn.close()
check("18.4 卡片表无残留", leftover == 0, f"leftover={leftover}")

# ═══════════════════════ v2.1：科研数据模块扩展 ═══════════════════════
# 19~22：ResearchQuestion 新字段 / PaperNote 证据片段 / Experiment 设计字段 /
# Run 复现字段 / ResearchDecision 决策记录

code, proj = call("POST", "/projects", {
    "name": MARKER + "v2.1数据模块",
    "goal": "验证研究问题目标假设、证据片段、复现字段与科研决策",
    "deadline": "2027-06-30",
    "weeklyHours": 10,
})
check("19.1 创建 v2.1 测试项目", code == 201, f"code={code}")
pid = proj["id"]

# ── 20. ResearchQuestion：目标/假设 ──────────────────────────────────
code, q = call("POST", f"/projects/{pid}/questions", {
    "content": "方法A是否在数据集X上优于方法B？",
    "objective": "为目标场景选出精度最高的方法",
    "hypothesis": "方法A的精度高于方法B至少2个百分点",
})
check("20.1 创建问题（含目标与假设）", code == 201 and q["objective"]
      and q["hypothesis"], f"code={code}")
qid = q["id"]

code, body = call("POST", f"/projects/{pid}/questions", {"content": "x", "objective": "目" * 2001})
check("20.2 目标超长 → 422", code == 422 and detail_contains(body, "研究目标"), f"code={code}")

code, q = call("PUT", f"/questions/{qid}", {"hypothesis": "方法A精度高2~3个百分点（修订）"})
check("20.3 更新假设", code == 200 and "修订" in q["hypothesis"], f"code={code}")

code, body = call("GET", f"/projects/{pid}/questions")
check("20.4 列表包含目标与假设字段", code == 200 and body[0]["objective"] and body[0]["hypothesis"], f"code={code}")

# ── 21. PaperNote（文献卡片）：创新点 + 原文证据片段及页码 ────────────
code, card = call("POST", f"/projects/{pid}/cards", {
    "title": "方法A论文",
    "innovations": "提出自适应模块A",
    "questionId": qid,
    "evidenceSnippets": [
        {"quote": "方法A在数据集X上取得87.3%的精度", "page": "5"},
        {"quote": "相比基线平均提升2.1个百分点", "page": "6-7"},
    ],
})
check("21.1 创建卡片（创新点+证据片段页码）", code == 201 and "自适应" in card["innovations"]
      and len(card["evidenceSnippets"]) == 2 and card["evidenceSnippets"][1]["page"] == "6-7", f"code={code}")
card_id = card["id"]

code, body = call("POST", f"/projects/{pid}/cards", {
    "title": "x", "evidenceSnippets": [{"quote": "", "page": "1"}],
})
check("21.2 空证据片段原文 → 422", code == 422 and detail_contains(body, "证据片段原文"), f"code={code}")

code, body = call("POST", f"/projects/{pid}/cards", {
    "title": "x", "evidenceSnippets": [{"quote": "原文摘录", "page": "x" * 21}],
})
check("21.3 页码超长 → 422", code == 422 and detail_contains(body, "页码"), f"code={code}")

code, card = call("PUT", f"/cards/{card_id}", {
    "evidenceSnippets": [{"quote": "方法A在数据集X上取得87.3%的精度", "page": "5"}],
})
check("21.4 更新证据片段", code == 200 and len(card["evidenceSnippets"]) == 1
      and card["source"] == "manual", f"code={code}")

code, body = call("GET", f"/projects/{pid}/cards")
card_back = next((c for c in body if c["id"] == card_id), None)
check("21.5 证据片段回读（列表接口）", code == 200 and card_back is not None
      and len(card_back["evidenceSnippets"]) == 1
      and card_back["evidenceSnippets"][0]["page"] == "5", f"code={code}")

# ── 22. Experiment：变量/对照/数据集/模型/配置 ──────────────────────
code, exp = call("POST", f"/projects/{pid}/experiments", {
    "title": "方法A vs 方法B",
    "objective": "验证方法A优于方法B",
    "hypothesis": "A的精度更高",
    "variables": "模型结构（A/B）、学习率（0.001/0.0005）",
    "controlConditions": "相同数据划分、相同训练轮数",
    "dataset": "数据集X（训练8:验证2）",
    "model": "方法A、方法B",
    "config": {"epochs": 50, "batchSize": 32},
    "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True}],
    "questionId": qid,
    "status": "running",
})
check("22.1 创建实验（变量/对照/数据集/模型/配置）", code == 201 and exp["variables"]
      and exp["dataset"] and exp["config"]["epochs"] == 50, f"code={code}")
eid = exp["id"]

code, body = call("POST", f"/projects/{pid}/experiments", {
    "title": "x", "objective": "x", "config": "not-a-dict",
})
check("22.2 配置非对象 → 422", code == 422, f"code={code}")

# ── 23. Run：随机种子/Git提交/环境/日志/结果文件 ─────────────────────
code, run = call("POST", f"/experiments/{eid}/runs", {
    "config": {"lr": 0.001},
    "results": {"Accuracy": 87.3},
    "randomSeed": 42,
    "gitCommit": "a1b2c3d4e5f6",
    "environment": {"python": "3.12.3", "torch": "2.4.0"},
    "logPath": "D:/logs/exp1-run1.log",
    "resultFiles": ["D:/results/exp1-run1.csv", "D:/results/exp1-run1.png"],
    "notes": "第一次完整运行",
})
check("23.1 新增运行记录（种子/提交/环境/日志/结果文件）", code == 201
      and run["randomSeed"] == 42 and run["gitCommit"] == "a1b2c3d4e5f6"
      and run["environment"]["torch"] == "2.4.0" and len(run["resultFiles"]) == 2, f"code={code}")
run_id = run["id"]

code, body = call("POST", f"/experiments/{eid}/runs", {"randomSeed": -1})
check("23.2 负随机种子 → 422", code == 422 and detail_contains(body, "随机种子"), f"code={code}")

code, body = call("POST", f"/experiments/{eid}/runs", {"gitCommit": "x" * 65})
check("23.3 Git 提交超长 → 422", code == 422 and detail_contains(body, "Git Commit"), f"code={code}")

code, body = call("POST", f"/experiments/{eid}/runs", {"resultFiles": [123]})
check("23.4 结果文件路径非字符串 → 422", code == 422, f"code={code} body={body}")

code, run = call("PUT", f"/runs/{run_id}", {"logPath": "D:/logs/exp1-run1-revised.log", "randomSeed": 43})
check("23.5 更新日志路径与种子", code == 200 and run["logPath"].endswith("revised.log")
      and run["randomSeed"] == 43, f"code={code}")

code, body = call("GET", f"/experiments/{eid}")
run_out = next((r for r in body["runs"] if r["id"] == run_id), None)
check("23.6 详情包含全部 v2.1 字段", code == 200 and run_out and run_out["environment"]
      and run_out["resultFiles"], f"code={code}")

# ── 24. ResearchDecision：科研决策记录 ───────────────────────────────
code, d = call("POST", f"/experiments/{eid}/decisions", {
    "runIds": [run_id],
    "observations": "第1次运行 Accuracy=87.3%，比基线高2.1个百分点",
    "interpretation": "方法A在本次运行中表现优于基线，与假设方向一致",
    "supportsHypothesis": True,
    "unknowns": "单次运行，未做多次重复验证；不同随机种子下的稳定性未知",
    "nextSuggestions": ["更换种子重复 3 次验证稳定性", "补充消融实验"],
})
check("24.1 创建科研决策（支持假设）", code == 201 and d["supportsHypothesis"] is True
      and len(d["runIds"]) == 1 and len(d["nextSuggestions"]) == 2, f"code={code}")
decision_id = d["id"]

code, body = call("POST", f"/experiments/{eid}/decisions", {
    "runIds": [], "observations": "x",
})
check("24.2 空关联记录 → 422", code == 422 and detail_contains(body, "运行记录"), f"code={code}")

code, body = call("POST", f"/experiments/{eid}/decisions", {
    "runIds": [99999], "observations": "x",
})
check("24.3 引用不存在的记录 → 400", code == 400 and detail_contains(body, "不存在"), f"code={code}")

# 跨实验引用校验：创建第二个实验，用它的 run 去建第一个实验的决策 → 400
code, exp2 = call("POST", f"/projects/{pid}/experiments", {
    "title": "另一个实验", "objective": "用于校验跨实验引用", "status": "draft",
})
code, run2 = call("POST", f"/experiments/{exp2['id']}/runs", {"results": {"x": 1}})
code, body = call("POST", f"/experiments/{eid}/decisions", {
    "runIds": [run2["id"]], "observations": "x",
})
check("24.4 跨实验引用 → 400", code == 400 and detail_contains(body, "不属于"), f"code={code}")

code, d = call("PUT", f"/decisions/{decision_id}", {
    "supportsHypothesis": False,
    "unknowns": "进一步复现后否定假设；稳定性不足",
})
check("24.5 更新决策（否定假设）", code == 200 and d["supportsHypothesis"] is False, f"code={code}")

code, d = call("PUT", f"/decisions/{decision_id}", {"supportsHypothesis": None})
check("24.6 假设判定置为待定（null）", code == 200 and d["supportsHypothesis"] is None, f"code={code}")

code, body = call("POST", f"/experiments/{eid}/decisions", {"observations": " "})
check("24.7 空观察到的事实 → 422", code == 422 and detail_contains(body, "观察到的事实"), f"code={code}")

code, body = call("POST", f"/experiments/{eid}/decisions", {
    "runIds": [run_id], "observations": "x", "nextSuggestions": ["a" * 501],
})
check("24.8 建议超长 → 422", code == 422 and detail_contains(body, "建议"), f"code={code}")

code, body = call("GET", f"/experiments/{eid}/decisions")
check("24.9 实验决策列表", code == 200 and len(body) >= 1 and body[0]["id"] == decision_id, f"code={code}")

code, body = call("GET", f"/projects/{pid}/decisions")
check("24.10 项目决策列表", code == 200 and any(x["id"] == decision_id for x in body), f"code={code}")

code, body = call("GET", "/decisions/99999")
check("24.11 不存在的决策 → 404", code == 404 and detail_contains(body, "决策记录不存在"), f"code={code}")

code, body = call("GET", f"/decisions/{decision_id}")
check("24.12 决策详情含全部字段", code == 200 and "observations" in body
      and "interpretation" in body and "nextSuggestions" in body, f"code={code}")

code, body = call("DELETE", f"/decisions/{decision_id}")
check("24.13 删除决策", code == 204)
code, body = call("GET", f"/decisions/{decision_id}")
check("24.14 删除后查询 → 404", code == 404)

# ── 25. v2.1 清理（级联） ───────────────────────────────────────────
code, body = call("DELETE", f"/projects/{pid}")
check("25.1 删除 v2.1 项目（级联清理）", code == 204)
conn = sqlite3.connect(DB_PATH)
leftover = conn.execute(
    "SELECT COUNT(*) FROM research_decision WHERE project_id = ?", (pid,)
).fetchone()[0]
leftover2 = conn.execute(
    "SELECT COUNT(*) FROM literature_card WHERE project_id = ?", (pid,)
).fetchone()[0]
conn.close()
check("25.2 决策与卡片表无残留", leftover == 0 and leftover2 == 0, f"leftover={leftover},{leftover2}")

# ═══════════════════════ v2.2：AI 研究分析 ═══════════════════════
# 26~29：无数据 400 / 演示模式生成（统计真实）/ 历史与详情 / 建议转任务
# 无 Key 环境下演示模式路径可确定性测试；AI 生成路径由单元测试覆盖。

code, proj = call("POST", "/projects", {
    "name": MARKER + "v2.2研究分析",
    "goal": "验证按研究问题聚合分析",
    "deadline": "2027-06-30",
    "weeklyHours": 10,
})
check("26.1 创建 v2.2 测试项目", code == 201, f"code={code}")
pid = proj["id"]

code, q = call("POST", f"/projects/{pid}/questions", {
    "content": "方法A是否优于方法B？", "hypothesis": "A 的精度更高",
})
qid = q["id"]

# 无实验数据 → 400 明确提示
code, body = call("POST", f"/questions/{qid}/analysis")
check("26.2 无实验数据分析 → 400 明确提示", code == 400
      and detail_contains(body, "当前缺少实验数据"), f"code={code} body={body}")

# 关联实验 + 运行记录 + 证据片段
code, card = call("POST", f"/projects/{pid}/cards", {
    "title": "对比论文", "questionId": qid,
    "evidenceSnippets": [{"quote": "方法A在数据集X上取得87.3%的精度", "page": "5"}],
})
code, exp = call("POST", f"/projects/{pid}/experiments", {
    "title": "A vs B", "objective": "对比", "questionId": qid, "status": "running",
    "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True}],
})
eid = exp["id"]
call("POST", f"/experiments/{eid}/runs", {"results": {"Accuracy": 80.0}})
code, run2 = call("POST", f"/experiments/{eid}/runs", {"results": {"Accuracy": 88.0}})

# 生成分析（无 Key → 演示模式；有 Key → DeepSeek 真实分析，双模式兼容）
code, analysis = call("POST", f"/questions/{qid}/analysis")
check("26.3 生成分析（演示/真实双模式）", code == 200 and analysis["source"] in ("demo", "deepseek")
      and analysis["hypothesisStatus"] in ("support", "not_support", "insufficient_evidence"),
      f"code={code} source={analysis.get('source') if code == 200 else '-'}")
analysis_id = analysis["id"] if code == 200 else None
if analysis_id:
    # 事实引用必须是真实存在的运行记录
    fact_run_ids = {f["experimentRunId"] for f in analysis["observedFacts"]}
    real_run_ids = {run2["id"], analysis["runIds"][0]}
    check("26.4 事实引用真实运行记录", code == 200 and fact_run_ids and fact_run_ids <= real_run_ids,
          f"facts={fact_run_ids} real={real_run_ids}")
    # 统计为后端确定性计算（min/max/mean 正确）
    m = analysis["stats"]["metrics"][0]["experiments"][0]
    check("26.5 统计数值确定性正确", m["min"] == 80.0 and m["max"] == 88.0 and m["mean"] == 84.0,
          f"stats={m}")
    # 文献证据引用真实卡片与片段
    if analysis["paperEvidence"]:
        ev = analysis["paperEvidence"][0]
        check("26.6 证据引用真实卡片/片段/页码", ev["paperNoteId"] == card["id"]
              and ev["snippetId"] == f"{card['id']}-1" and ev["page"] == "5",
              f"ev={ev}")
    else:
        print("[SKIP] 26.6 演示证据为空（卡片片段存在但模板未引用），跳过")

    # 历史与详情
    code, body = call("GET", f"/questions/{qid}/analyses")
    check("26.7 分析历史", code == 200 and any(a["id"] == analysis_id for a in body), f"code={code}")
    code, body = call("GET", f"/research-analyses/{analysis_id}")
    check("26.8 分析详情", code == 200 and body["id"] == analysis_id, f"code={code}")
    code, body = call("GET", "/research-analyses/99999")
    check("26.9 不存在的分析 → 404", code == 404 and detail_contains(body, "分析记录不存在"), f"code={code}")

    # 建议转任务：夹具注入带建议的分析（演示模式的建议已存在，直接用）
    suggestions = json.loads(analysis["nextExperiments"]) if isinstance(analysis.get("nextExperiments"), str) else analysis["nextExperiments"]
    if suggestions:
        code, result = call("POST", f"/research-analyses/{analysis_id}/suggestions/0/to-task")
        check("26.10 建议转任务（来源标记）", code == 201
              and result["task"]["sourceType"] == "research_analysis"
              and result["task"]["sourceId"] == analysis_id, f"code={code}")
        code, body = call("POST", f"/research-analyses/{analysis_id}/suggestions/0/to-task")
        check("26.11 重复转换 → 400（防重复）", code == 400 and detail_contains(body, "已转换"), f"code={code}")
        code, body = call("POST", f"/research-analyses/{analysis_id}/suggestions/9/to-task")
        check("26.12 不存在的建议 → 404", code == 404, f"code={code}")
    else:
        print("[SKIP] 26.10~26.12 演示建议为空，跳过转任务断言")

code, body = call("DELETE", f"/projects/{pid}")
check("26.13 删除 v2.2 项目（级联清理）", code == 204)

# ═══════════════════════ v2.3：决策 → 执行计划完整链路 ═══════════════════════
# 27：分析建议 → 修改留档 → 采纳（实验+任务）→ 风险预警 → 重规划 →
#      守卫验证（不碰假设/结果）→ 历史记录 → 拒绝

code, proj = call("POST", "/projects", {
    "name": MARKER + "v2.3决策执行闭环",
    "goal": "验证决策到任务、风险、重规划全链路",
    "deadline": "2027-06-30",
    "weeklyHours": 10,
})
check("27.1 创建闭环测试项目", code == 201, f"code={code}")
pid = proj["id"]

code, q = call("POST", f"/projects/{pid}/questions", {
    "content": "方法A是否优于方法B？", "hypothesis": "A 的精度更高",
})
qid = q["id"]
code, exp = call("POST", f"/projects/{pid}/experiments", {
    "title": "方法A复现", "objective": "复现", "questionId": qid, "status": "running",
    "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True}],
})
eid = exp["id"]
_, run1 = call("POST", f"/experiments/{eid}/runs", {"results": {"Accuracy": 82.0}})
call("POST", f"/experiments/{eid}/runs", {"results": {"Accuracy": 84.0}})

# 生成分析（演示模式 → 模板建议）
_, analysis = call("POST", f"/questions/{qid}/analysis")
aid = analysis["id"]
check("27.2 生成分析（含模板建议）", len(analysis["nextExperiments"]) >= 1, f"len={len(analysis['nextExperiments'])}")

# 用户修改建议（不采纳）→ 留档
code, body = call("PUT", f"/research-analyses/{aid}/suggestions/0", {
    "objective": "验证方法A去掉模块A后的精度变化", "estimatedEffort": "3天",
})
check("27.3 修改建议并留档", code == 200 and "模块A" in body["objective"], f"code={code}")

# 手工创建一个未完成的前置任务（依赖阻塞用）
code, prereq = call("POST", "/tasks", {"projectId": pid, "title": "准备数据集X（未完成）"})
check("27.4 创建前置任务", code == 201, f"code={code}")
prereq_id = prereq["id"]

# 采纳建议 0：逾期日期 + 依赖未完成前置 → 创建实验与任务
code, adopt = call("POST", f"/research-analyses/{aid}/suggestions/0/adopt", {
    "objective": "验证方法A去掉模块A后的精度变化",
    "hypothesis": "去掉模块A后精度下降",
    "variables": "是否包含模块A",
    "requiredData": "数据集X（训练/验证划分）",
    "preconditions": "数据集X准备完成",
    "estimatedHours": 12.0,
    "plannedStartDate": "2026-10-01",
    "plannedEndDate": "2026-10-15",   # 已过期 → 逾期高风险
    "dependencies": [prereq_id],
})
check("27.5 采纳建议 → 创建实验+任务", code == 201
      and adopt["experiment"]["hypothesis"] == "去掉模块A后精度下降"
      and adopt["task"]["experimentId"] == adopt["experiment"]["id"]
      and adopt["log"]["action"] == "adopted", f"code={code}")
task0_id = adopt["task"]["id"] if code == 201 else None
exp_new_id = adopt["experiment"]["id"] if code == 201 else None

if task0_id:
    code, body = call("GET", f"/projects/{pid}")
    t0 = next(t for t in body["tasks"] if t["id"] == task0_id)
    check("27.6 任务保存实验/问题/日期/依赖", t0["experimentId"] == exp_new_id
          and t0["questionId"] == qid and t0["plannedEndDate"] == "2026-10-15"
          and t0["dependencies"] == [prereq_id] and t0["sourceType"] == "research_analysis",
          f"task={t0}")
    check("27.7 风险引擎识别逾期（高风险）", t0["risk"] == "high" and "逾期" in t0["riskReason"],
          f"risk={t0['risk']} reason={t0['riskReason']}")

    # 追加第二条建议（夹具）并采纳：未来日期 + 依赖未完成前置 → 前置阻塞
    conn = sqlite3.connect(DB_PATH)
    suggestions = json.loads(conn.execute(
        "SELECT next_experiments_json FROM research_analysis WHERE id = ?", (aid,)
    ).fetchone()[0])
    suggestions.append({"objective": "第二次建议实验", "hypothesis": "假设2",
                        "changed_variables": "", "fixed_conditions": "", "metrics": "Accuracy",
                        "expected_observation": "", "risks": "", "estimated_effort": "1天",
                        "converted": False})
    conn.execute("UPDATE research_analysis SET next_experiments_json = ? WHERE id = ?",
                 (json.dumps(suggestions, ensure_ascii=False), aid))
    conn.commit()
    conn.close()

    code, adopt2 = call("POST", f"/research-analyses/{aid}/suggestions/1/adopt", {
        "objective": "第二次建议实验",
        "hypothesis": "假设2",
        "estimatedHours": 6.0,
        "plannedStartDate": "2027-01-10",
        "plannedEndDate": "2027-01-20",
        "dependencies": [prereq_id],
    })
    task1_id = adopt2["task"]["id"] if code == 201 else None
    check("27.8 第二条建议采纳", code == 201, f"code={code}")

    code, body = call("GET", f"/projects/{pid}")
    t1 = next(t for t in body["tasks"] if t["id"] == task1_id)
    check("27.9 风险引擎识别前置阻塞（中风险）", t1["risk"] == "medium" and "前置" in t1["riskReason"],
          f"risk={t1['risk']} reason={t1['riskReason']}")

    # 记录实验快照（守卫验证用）
    _, exp_before = call("GET", f"/experiments/{exp_new_id}")
    _, e_before = call("GET", f"/experiments/{eid}")
    hypothesis_before = exp_before["experiment"]["hypothesis"]
    results_before = [r["results"] for r in e_before["runs"]]

    # 动态重规划（无 Key → 本地规则：逾期任务顺延+提优先级）
    code, replan = call("POST", f"/projects/{pid}/replan")
    check("27.10 生成重规划方案", code == 200 and len(replan["changes"]) >= 1, f"code={code}")
    replan_id = replan["id"]
    code, body = call("POST", f"/replans/{replan_id}/adopt")
    check("27.11 采纳重规划", code == 200 and body["appliedCount"] >= 1, f"code={code}")

    # 守卫验证 1：任务日期被调整（逾期任务顺延到今天之后）
    code, body = call("GET", f"/projects/{pid}")
    t0_after = next(t for t in body["tasks"] if t["id"] == task0_id)
    check("27.12 重规划调整了任务执行日期", t0_after["plannedEndDate"] != "2026-10-15",
          f"after={t0_after['plannedEndDate']}")

    # 守卫验证 2：研究假设与实验结果未被重规划触碰
    _, exp_after = call("GET", f"/experiments/{exp_new_id}")
    _, e_after = call("GET", f"/experiments/{eid}")
    check("27.13 重规划未修改研究假设", exp_after["experiment"]["hypothesis"] == hypothesis_before,
          f"before={hypothesis_before} after={exp_after['experiment']['hypothesis']}")
    check("27.14 重规划未修改实验结果", [r["results"] for r in e_after["runs"]] == results_before,
          f"before={results_before} after={[r['results'] for r in e_after['runs']]}")

    # 追加第三条建议（夹具）→ 拒绝 → 留档；拒绝后不可采纳
    conn = sqlite3.connect(DB_PATH)
    suggestions = json.loads(conn.execute(
        "SELECT next_experiments_json FROM research_analysis WHERE id = ?", (aid,)
    ).fetchone()[0])
    suggestions.append({"objective": "第三条建议", "hypothesis": "假设3",
                        "changed_variables": "", "fixed_conditions": "", "metrics": "Accuracy",
                        "expected_observation": "", "risks": "", "estimated_effort": "1天",
                        "converted": False})
    conn.execute("UPDATE research_analysis SET next_experiments_json = ? WHERE id = ?",
                 (json.dumps(suggestions, ensure_ascii=False), aid))
    conn.commit()
    conn.close()
    code, log = call("POST", f"/research-analyses/{aid}/suggestions/2/reject", {"reason": "方向调整，暂不做"})
    check("27.15 拒绝建议并留档", code == 200 and log["action"] == "rejected", f"code={code}")
    code, body = call("POST", f"/research-analyses/{aid}/suggestions/2/adopt", {
        "objective": "x", "hypothesis": "y", "estimatedHours": 1,
        "plannedStartDate": "2027-02-01", "plannedEndDate": "2027-02-10",
    })
    check("27.16 已拒绝建议不可采纳 → 400", code == 400 and detail_contains(body, "拒绝"), f"code={code}")

    # 历史记录：modified + adopted×2 + rejected 全部可查
    code, logs = call("GET", f"/research-analyses/{aid}/actions")
    actions = [x["action"] for x in logs]
    check("27.17 采纳/拒绝/修改全部留档", code == 200
          and "modified" in actions and actions.count("adopted") == 2 and "rejected" in actions,
          f"actions={actions}")

    # 采纳后防重复
    code, body = call("POST", f"/research-analyses/{aid}/suggestions/0/adopt", {
        "objective": "x", "hypothesis": "y", "estimatedHours": 1,
        "plannedStartDate": "2027-02-01", "plannedEndDate": "2027-02-10",
    })
    check("27.18 重复采纳 → 400", code == 400 and detail_contains(body, "已采纳"), f"code={code}")

code, body = call("DELETE", f"/projects/{pid}")
check("27.19 删除闭环项目（级联清理）", code == 204)
conn = sqlite3.connect(DB_PATH)
leftover = conn.execute(
    "SELECT COUNT(*) FROM research_action_log WHERE project_id = ?", (pid,)
).fetchone()[0]
conn.close()
check("27.20 操作历史表无残留", leftover == 0, f"leftover={leftover}")

print(f"\n===== 通过 {passed} 项，失败 {failed} 项 =====")
sys.exit(1 if failed else 0)
