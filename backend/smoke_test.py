# -*- coding: utf-8 -*-
"""后端接口冒烟测试：CRUD + 入参校验 + 错误处理 + 持久化。

用法（需后端已启动）：
    venv\\Scripts\\python smoke_test.py [base_url]

默认 base_url = http://127.0.0.1:8000，可指定其他端口/代理地址。
脚本只创建/删除名称带「【冒烟测试】」前缀的数据，不会碰其他数据。
"""
import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = BASE.rstrip("/") + "/api"

MARKER = "【冒烟测试】"


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

print(f"\n===== 通过 {passed} 项，失败 {failed} 项 =====")
sys.exit(1 if failed else 0)
