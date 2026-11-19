# -*- coding: utf-8 -*-
"""ResearchPilot v2 数据迁移脚本（幂等，可重复执行）。

作用：
1. 迁移前自动备份 research.db → research.db.bak-v2（仅首次）；
2. 为既有表新增 v2 / v2.1 列（列已存在则跳过，绝不删除旧列）；
3. 新增表（research_question / literature_card / experiment / experiment_run /
   experiment_analysis / research_decision）由 init_db() 的 create_all 自动创建，
   无需本脚本处理。

用法（在 backend 目录下）：
    venv\\Scripts\\python migrate_v2.py
"""
import sqlite3
import shutil
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "research.db"
BACKUP_PATH = Path(__file__).resolve().parent / "research.db.bak-v2"

# 每张表的加列清单：(表名, [(列名, SQL 类型), ...])
TABLE_COLUMNS = {
    "task": [
        ("source_type", "TEXT"),   # v2 任务来源类型
        ("source_id", "INTEGER"),  # v2 来源实体 id（可空）
        ("experiment_id", "INTEGER"),              # v2.3 所属实验
        ("question_id", "INTEGER"),                # v2.3 所属研究问题
        ("dependencies_json", "TEXT NOT NULL DEFAULT '[]'"),  # v2.3 依赖任务 id 列表
    ],
    "research_question": [
        ("objective", "TEXT"),     # v2.1 研究目标
        ("hypothesis", "TEXT"),    # v2.1 研究假设
    ],
    "literature_card": [
        ("innovations", "TEXT"),                # v2.1 创新点
        ("evidence_snippets_json", "TEXT NOT NULL DEFAULT '[]'"),  # v2.1 原文证据片段及页码
    ],
    "experiment": [
        ("variables", "TEXT"),                  # v2.1 实验变量
        ("control_conditions", "TEXT"),         # v2.1 对照条件
        ("dataset", "TEXT"),                    # v2.1 数据集
        ("model", "TEXT"),                      # v2.1 模型
        ("config_json", "TEXT NOT NULL DEFAULT '{}'"),  # v2.1 实验配置
    ],
    "experiment_run": [
        ("random_seed", "INTEGER"),             # v2.1 随机种子
        ("git_commit", "VARCHAR(64)"),          # v2.1 代码 Git Commit
        ("environment_json", "TEXT NOT NULL DEFAULT '{}'"),  # v2.1 环境信息
        ("log_path", "VARCHAR(500)"),           # v2.1 日志路径
        ("result_files_json", "TEXT NOT NULL DEFAULT '[]'"),  # v2.1 结果文件路径
    ],
}


def main() -> int:
    if not DB_PATH.exists():
        print(f"[跳过] 数据库文件不存在：{DB_PATH}（首次启动时由后端自动创建，无需迁移）")
        return 0

    # 1. 备份（仅首次，不覆盖已有备份）
    if not BACKUP_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"[备份] 已备份 {DB_PATH.name} → {BACKUP_PATH.name}")
    else:
        print(f"[备份] 已存在备份 {BACKUP_PATH.name}，跳过")

    # 2. 逐表逐列加列（幂等：列已存在则跳过）
    conn = sqlite3.connect(DB_PATH)
    added = 0
    try:
        existing_tables = {
            row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for table, columns in TABLE_COLUMNS.items():
            if table not in existing_tables:
                print(f"[跳过] 表 {table} 不存在（将由后端启动时自动创建）")
                continue
            existing_cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name, sql_type in columns:
                if name in existing_cols:
                    print(f"[跳过] {table}.{name} 已存在")
                    continue
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")
                print(f"[完成] 表 {table} 新增列 {name} ({sql_type})")
                added += 1
        conn.commit()
        if added == 0:
            print("[结果] 无需变更，全部列已是最新结构")
        else:
            print(f"[结果] 迁移完成，共新增 {added} 列")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
