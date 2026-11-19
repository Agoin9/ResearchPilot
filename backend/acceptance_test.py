# -*- coding: utf-8 -*-
"""ResearchPilot 2.0 质量验收端到端脚本（10 个关键业务场景）。

用法（需后端已启动，默认 http://127.0.0.1:8000）：
    venv\\Scripts\\python acceptance_test.py [base_url]

特点：
- 全部数据以「【验收】」标记，脚本结束自动清理（--keep 保留供人工复查）；
- 每个场景独立编号输出 [PASS]/[FAIL]/[SKIP] + 失败原因；
- 场景 5 的实验数据为明确标记的【演示】数据（无真实实验数据）；
- 场景 7 的 DeepSeek 调用按当前密钥配置自动区分：无 Key → 演示模式；
  无效 Key → 502 友好错误；真实 Key → 真实分析（断网时记录 502 原因）。
"""
import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
API = BASE.rstrip("/") + "/api"
KEEP = "--keep" in sys.argv

MARKER = "【验收】"
results = []


def record(name, ok, detail=""):
    status = "PASS" if ok else "FAIL"
    results.append((status, name, detail))
    print(f"[{status}] {name} {detail}" if detail else f"[{status}] {name}")


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode("utf-8") if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw) if raw else None
        except ValueError:
            return e.code, {"detail": raw.decode("utf-8", errors="replace")[:200]}
    except urllib.error.URLError as e:
        return 0, {"detail": f"网络错误: {e.reason}"}


def call_upload(path, filename, content_type, data):
    boundary = "----acceptanceboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(API + path, method="POST", data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw) if raw else None
        except ValueError:
            return e.code, {"detail": raw.decode("utf-8", errors="replace")[:200]}


# ═══════════════════════ 最小合法 PDF 生成（含真实文字层） ═══════════════════════

def build_test_pdf() -> bytes:
    """手工构造含文字层的合法 PDF（ASCII 文本，pypdf 可提取）。"""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
         b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        None,  # 5 0 obj 内容流（含流长度，稍后填充）
    ]
    stream = (
        b"BT /F1 12 Tf 72 720 Td "
        b"(Method A achieves 87.3% accuracy on dataset X.) Tj "
        b"0 -20 Td (Baseline method B achieves 80.1% accuracy.) Tj "
        b"0 -20 Td (We propose an adaptive module to improve accuracy.) Tj ET"
    )
    objects[4] = b"<< /Length %d >> stream\n" % len(stream) + stream + b"\nendstream"

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for pos in offsets:
        out += f"{pos:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode()
    return bytes(out)


# ═══════════════════════ 场景执行 ═══════════════════════

def main():
    print(f"===== ResearchPilot 2.0 质量验收（{BASE}）=====\n")
    pid = None

    # ── 场景 1：创建科研项目和研究问题 ──
    code, proj = call("POST", "/projects", {
        "name": MARKER + "验收-科研项目",
        "goal": "验证方法A在数据集X上是否优于基线方法B",
        "deadline": "2027-06-30",
        "weeklyHours": 10,
    })
    ok1 = code == 201 and proj["id"] > 0
    record("场景1 创建科研项目", ok1, f"code={code}")
    if not ok1:
        print("无法继续，退出")
        sys.exit(1)
    pid = proj["id"]

    code, q = call("POST", f"/projects/{pid}/questions", {
        "content": "方法A是否在数据集X上优于基线方法B？",
        "objective": "为目标场景选择精度更高的方法",
        "hypothesis": "方法A的Accuracy高于方法B至少2个百分点",
    })
    qid = q["id"] if code == 201 else None
    record("场景1 创建研究问题（目标+假设）", code == 201 and q["objective"] and q["hypothesis"],
           f"code={code}")

    # ── 场景 2：上传可正常解析的 PDF ──
    pdf = build_test_pdf()
    code, doc = call_upload(
        f"/projects/{pid}/documents", "acceptance_paper.pdf", "application/pdf", pdf
    )
    ok2 = code == 201 and doc["chunkCount"] >= 1
    record("场景2 上传PDF并解析文字", ok2, f"code={code} chunks={doc.get('chunkCount') if doc else '-'}")
    doc_id = doc["id"] if ok2 else None

    # ── 场景 3：生成文献卡片，引用可定位到真实原文与页码 ──
    code, extract = call("POST", f"/documents/{doc_id}/card")
    ok_extract = code == 200 and extract["card"]["source"] in ("demo", "deepseek")
    record("场景3 AI抽取卡片（当前密钥模式下）", ok_extract,
           f"code={code} source={extract['card']['source'] if code == 200 else '-'}")
    card_id = extract["card"]["id"] if ok_extract else None

    code, card = call("PUT", f"/cards/{card_id}", {
        "title": "Method A paper (acceptance)",
        "method": "Adaptive module + standard training",
        "metrics": "Accuracy",
        "keyResults": "Method A achieves 87.3% accuracy on dataset X",
        "innovations": "Adaptive module",
        "questionId": qid,
        "evidenceSnippets": [
            {"quote": "Method A achieves 87.3% accuracy on dataset X.", "page": "1"},
            {"quote": "Baseline method B achieves 80.1% accuracy.", "page": "1"},
        ],
    })
    ok3a = code == 200 and len(card["evidenceSnippets"]) == 2
    record("场景3 人工完善卡片+证据片段页码", ok3a, f"code={code}")

    # 定位验证：片段原文必须真实存在于 PDF 提取的原文中（前端点击定位的底层保证）
    code, detail = call("GET", f"/documents/{doc_id}")
    full_text = detail.get("fullText", "") if code == 200 else ""
    located = all(
        sn["quote"] in full_text for sn in (card.get("evidenceSnippets", []) if ok3a else [])
    )
    record("场景3 证据片段可定位到真实原文", located,
           f"quotes_in_fulltext={located}")

    # ── 场景 4：根据文献创建实验设计 ──
    code, exp_a = call("POST", f"/projects/{pid}/experiments", {
        "title": MARKER + "【演示】方法A复现实验",
        "objective": "复现文献报告的方法A精度",
        "hypothesis": "方法A的Accuracy接近文献报告的87.3%",
        "variables": "是否启用自适应模块",
        "controlConditions": "相同数据划分与训练轮数",
        "dataset": "数据集X（演示数据）",
        "model": "方法A",
        "config": {"epochs": 50},
        "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True}],
        "questionId": qid,
        "status": "running",
    })
    code, exp_b = call("POST", f"/projects/{pid}/experiments", {
        "title": MARKER + "【演示】基线方法B复现实验",
        "objective": "复现基线方法B精度",
        "hypothesis": "方法B的Accuracy接近80.1%",
        "variables": "无",
        "controlConditions": "与方法A实验相同",
        "dataset": "数据集X（演示数据）",
        "model": "方法B",
        "metrics": [{"name": "Accuracy", "unit": "%", "higherIsBetter": True}],
        "questionId": qid,
        "status": "running",
    })
    ok4 = code == 201 and exp_a["variables"] and exp_b["dataset"]
    record("场景4 根据文献创建实验设计（变量/对照/数据集/模型/配置）", ok4, f"code={code}")
    eid_a, eid_b = exp_a["id"], exp_b["id"]

    # ── 场景 5：录入两组以上实验运行记录（明确标记的演示数据） ──
    # 数据为【演示】标记（无真实实验数据），脚本如实标注
    runs_a = [81.2, 85.9, 86.4]
    runs_b = [79.8, 80.3, 80.1]
    ok5 = True
    for values, eid, tag in [(runs_a, eid_a, "A"), (runs_b, eid_b, "B")]:
        for i, v in enumerate(values):
            code, run = call("POST", f"/experiments/{eid}/runs", {
                "config": {"epochs": 50, "seed": 42 + i},
                "results": {"Accuracy": v},
                "randomSeed": 42 + i,
                "notes": f"【演示】方法{tag}第{i + 1}次运行（演示数据，非真实实验）",
            })
            if code != 201:
                ok5 = False
                break
    record("场景5 录入两组实验运行记录（标记【演示】）", ok5, "3+3 次运行")

    # ── 场景 6：比较多组实验的真实指标 ──
    code, overview = call("GET", f"/projects/{pid}/metrics")
    metric = next((m for m in overview["metrics"] if m["name"] == "Accuracy"), None) if code == 200 else None
    ok6 = metric is not None and len(metric["points"]) == 6
    if ok6:
        best_a = max(p["value"] for p in metric["points"] if p["experimentId"] == eid_a)
        best_b = max(p["value"] for p in metric["points"] if p["experimentId"] == eid_b)
        ok6 = best_a == 86.4 and best_b == 80.3
    record("场景6 跨实验指标对比（真实数值）", ok6,
           f"points={len(metric['points']) if metric else '-'} bestA={best_a if ok6 else '-'}")

    # ── 场景 7：AI 研究分析（事实/推测/未知/建议 区分） ──
    code, analysis = call("POST", f"/questions/{qid}/analysis")
    if code == 200:
        facts = analysis["observedFacts"]
        evidence = analysis["paperEvidence"]
        interp = analysis.get("interpretation", "")
        unknown = analysis.get("uncertainty", "")
        suggestions = analysis["nextExperiments"]
        # 七段结构区分验证（解释必须含推测性标记词，与后端校验一致）
        speculation_markers = ("推测", "可能", "或许", "尚不", "待验证", "不确定", "演示模式")
        sections_ok = (
            len(facts) >= 1
            and all("experimentRunId" in f for f in facts)
            and any(m in interp for m in speculation_markers)
            and isinstance(suggestions, list)
            and analysis["hypothesisStatus"] in ("support", "not_support", "insufficient_evidence")
            and (unknown or analysis["hypothesisStatus"] == "insufficient_evidence")
        )
        record(
            "场景7 研究分析七段结构区分（事实/推测/未知/建议）",
            sections_ok,
            f"source={analysis['source']} facts={len(facts)} evidence={len(evidence)} "
            f"suggestions={len(suggestions)} status={analysis['hypothesisStatus']}",
        )
        # 演示模式必须有证据（模板确定性引用）；真实模式证据可为空（校验层保证
        # 非空证据必然引用真实卡片与片段——AI 找不到依据时允许返回空数组）
        if analysis["source"] == "demo":
            ev_ok = bool(evidence) and all(
                e["paperNoteId"] == card_id and e["page"] == "1" for e in evidence
            )
        else:
            ev_ok = all(
                e["paperNoteId"] == card_id and e["page"] == "1" for e in evidence
            )
        record(
            "场景7 文献证据引用真实卡片与片段",
            ev_ok,
            f"source={analysis['source']} evidence={[(e['paperNoteId'], e['snippetId'], e['page']) for e in evidence]}",
        )
        aid = analysis["id"]
        suggestion_count = len(suggestions)
    else:
        record("场景7 研究分析生成", False, f"code={code} body={analysis}")
        aid, suggestion_count = None, 0

    # ── 场景 8：用户确认一条建议 → Experiment + Task ──
    if aid and suggestion_count:
        code, adopt = call("POST", f"/research-analyses/{aid}/suggestions/0/adopt", {
            "objective": "【演示】验证自适应模块的消融效果",
            "hypothesis": "去掉自适应模块后Accuracy下降",
            "variables": "是否包含自适应模块",
            "requiredData": "数据集X（演示）",
            "preconditions": "方法A复现实验完成",
            "estimatedHours": 10.0,
            "plannedStartDate": (date.today() + timedelta(days=3)).isoformat(),
            "plannedEndDate": (date.today() + timedelta(days=17)).isoformat(),
            "dependencies": [],
        })
        ok8 = code == 201 and adopt["task"]["experimentId"] == adopt["experiment"]["id"]
        record("场景8 确认建议 → 创建Experiment+Task", ok8, f"code={code}")
        task8_id = adopt["task"]["id"] if ok8 else None
    else:
        record("场景8 确认建议 → 创建Experiment+Task", False, "场景7未产出分析，无法继续")
        task8_id = None

    # ── 场景 9：模拟任务延期 → 风险识别 → 动态重规划 ──
    code, delayed_task = call("POST", "/tasks", {
        "projectId": pid,
        "title": MARKER + "已延期任务",
        "plannedStartDate": "2026-10-01",
        "plannedEndDate": "2026-10-15",
        "estimatedHours": 8,
    })
    delayed_id = delayed_task["id"] if code == 201 else None
    code, body = call("GET", f"/projects/{pid}")
    delayed = next((t for t in body["tasks"] if t["id"] == delayed_id), None)
    ok9a = delayed is not None and delayed["risk"] == "high" and "逾期" in delayed["riskReason"]
    record("场景9 延期任务被风险引擎识别（高风险）", ok9a,
           f"risk={delayed['risk'] if delayed else '-'} reason={delayed['riskReason'] if delayed else '-'}")

    code, replan = call("POST", f"/projects/{pid}/replan")
    ok9b = code == 200 and len(replan["changes"]) >= 1
    record("场景9 生成动态重规划方案", ok9b, f"code={code} changes={len(replan['changes']) if code == 200 else '-'}")
    if ok9b:
        code, adopted = call("POST", f"/replans/{replan['id']}/adopt")
        ok9c = code == 200 and adopted["appliedCount"] >= 1
        record("场景9 采纳重规划（调整执行安排）", ok9c, f"applied={adopted.get('appliedCount') if code == 200 else '-'}")
        # 守卫：研究假设与实验结果不变
        _, exp_after = call("GET", f"/experiments/{eid_a}")
        _, detail_after = call("GET", f"/experiments/{eid_a}")
        results_after = [r["results"] for r in detail_after["runs"]]
        results_expected = [{"Accuracy": v} for v in runs_a]
        guard_ok = (
            exp_after["experiment"]["hypothesis"] == "方法A的Accuracy接近文献报告的87.3%"
            and results_after == results_expected
        )
        record("场景9 守卫：重规划未触碰假设与实验结果", guard_ok, f"results={results_after}")
    else:
        record("场景9 采纳重规划", False, "方案生成失败，跳过")

    # ── 场景 10：决策日志 / 实验历史 / 重规划历史 完整性 ──
    code, decision = call("POST", f"/experiments/{eid_a}/decisions", {
        "runIds": [],  # 先测校验
        "observations": "x",
    })
    record("场景10 决策空运行记录 → 422", code == 422, f"code={code}")

    _, runs_a_detail = call("GET", f"/experiments/{eid_a}")
    run_ids = [r["id"] for r in runs_a_detail["runs"]]
    code, decision = call("POST", f"/experiments/{eid_a}/decisions", {
        "runIds": run_ids,
        "observations": "【演示】方法A三次运行均值与文献报告接近（演示数据）",
        "interpretation": "复现结果与文献方向一致（演示判断）",
        "supportsHypothesis": True,
        "unknowns": "未做多次随机种子重复（演示数据）",
        "nextSuggestions": ["更换种子重复验证"],
    })
    ok10a = code == 201 and decision["id"] > 0
    record("场景10 创建研究决策", ok10a, f"code={code}")

    code, decisions = call("GET", f"/experiments/{eid_a}/decisions")
    ok10b = code == 200 and len(decisions) >= 1
    record("场景10 决策日志可查", ok10b, f"count={len(decisions) if code == 200 else '-'}")

    code, history = call("GET", f"/experiments/{eid_a}")
    ok10c = code == 200 and len(history["runs"]) == 3
    record("场景10 实验运行历史完整（3 次运行）", ok10c,
           f"runs={len(history['runs']) if code == 200 else '-'}")

    code, replans = call("GET", f"/projects/{pid}/replans")
    ok10d = code == 200 and len(replans) >= 1 and any(r["status"] == "adopted" for r in replans)
    record("场景10 重规划历史完整（含已采纳记录）", ok10d,
           f"count={len(replans) if code == 200 else '-'}")

    if aid:
        code, actions = call("GET", f"/research-analyses/{aid}/actions")
        record("场景10 建议操作历史完整", code == 200 and len(actions) >= 1,
               f"actions={[a['action'] for a in actions] if code == 200 else '-'}")

    # ── 汇总与清理 ──
    print()
    passed = sum(1 for s, _, _ in results if s == "PASS")
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    print(f"===== 验收结果：通过 {passed} 项，失败 {failed} 项 =====")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"  [FAIL] {name}：{detail}")

    if pid and not KEEP:
        call("DELETE", f"/projects/{pid}")
        code, _ = call("GET", f"/projects/{pid}")
        print(f"清理验收数据：{'完成' if code == 404 else f'失败 code={code}'}")
    elif pid:
        print(f"验收数据保留（项目 id={pid}），可在界面复查")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
