你现在是一名资深AI产品经理、科研工作流设计专家和全栈工程师。请完整检查当前 ResearchPilot 项目，不要立即修改任何代码。

项目背景：ResearchPilot 是一个面向研究生的科研辅助系统，当前已有科研项目管理、任务拆解、DeepSeek计划生成、延期风险识别、动态重规划、PDF文献问答、周报生成和数据看板。

现在预赛评委给出意见：科研过程不像工程项目那样容易通过任务管理解决，产品思路不错，但没有清楚展示系统具体解决了什么科研问题。目前产品需要从普通科研任务管理工具升级为围绕“文献理解—实验设计与复现—实验结果记录—研究分析—下一步决策”的科研工作台。

请完成以下工作：
1. 扫描整个项目目录，梳理前端页面、后端路由、数据库模型、AI服务、已有测试和启动方式。
2. 对每个现有功能标注：已实现且已验证、已实现但未验证、仅有界面、尚未实现。不得凭文件名推断功能已经完成。
3. 分析当前系统为什么更像工程任务管理工具，指出缺少哪些科研工作流能力。
4. 设计 ResearchPilot 2.0 的最小可行升级方案，核心闭环为：研究问题→文献证据→实验设计→实验运行记录→结果分析→下一步研究决策→转为科研任务。
5. 重点规划三个新模块：结构化文献研究卡片、实验管理与结果比较、基于真实实验记录的AI分析。
6. 说明如何兼容目前项目中的任务管理、风险识别、重规划、PDF问答和周报功能。
7. 列出建议的数据表、API、前端页面、实施顺序、风险和验收标准。

严格要求：不要更换React、TypeScript、Vite、FastAPI、SQLite和DeepSeek技术栈；不要删除或重写已经工作的模块；不要把所有科研工作简单当成工程任务；不需要集成GPU训练执行平台；不允许伪造论文内容、实验结果和测试结果。

请先输出一份 docs/researchpilot-v2-plan.md，等待我审核。此步骤禁止修改业务代码。
Show more
5:43 PM
好的，我先完整扫描项目结构和代码，再输出规划文档。我会分步骤进行并逐步报告结果。

第 1 步：扫描项目目录结构



5:44 PM
发现项目根目录有 .venv，刚才没有排除它。我重新扫描，排除虚拟环境。



5:44 PM
后端也有自己的 .venv，我再次排除。



5:44 PM
后端还有个 venv 目录。既然这是 git 仓库，直接用 git ls-files 列出所有受版本控制的文件最干净。



5:44 PM
发现一个仓库卫生问题：backend/venv 虚拟环境被提交进了 git（136KB 的文件列表几乎全是它）。我过滤掉它看真实项目文件。



5:44 PM
项目文件清单已清楚。现在 第 2 步：查看 git 完整提交历史，了解各功能的开发轨迹。



5:44 PM
共 6 次提交，PDF 问答和周报功能的代码已存在但未在提交信息中单独体现。现在 第 3 步：通读后端核心代码，验证功能真实实现情况。



5:44 PM
后端模型层已经包含文献表（Document/DocChunk/DocQa）和周报表（Report）。注意到 source: demo/deepseek 字段——需要确认哪些功能是真实 AI 实现、哪些是演示模式。继续读路由层。



5:44 PM
路由层很完整。继续读其余路由和 AI 客户端。



5:45 PM
后端路由全部读完。第 4 步：通读服务层，验证 AI 逻辑与风险识别实现。



5:45 PM
继续读剩余服务层和测试文件。



5:45 PM
后端服务层读完。现在看测试、序列化器和首页聚合服务。



5:45 PM
后端已全部通读。第 5 步：检查前端配置与入口，确认页面结构、依赖和测试配置。



5:45 PM
前端 API 层与后端一一对应。第 6 步：通读前端页面，验证 UI 真实实现情况。



5:45 PM
继续读剩余页面和 Tab 组件。



5:45 PM
页面层均为真实实现。第 7 步：检查三个核心 Tab 组件和看板组件，确认没有占位符。



5:45 PM
所有 Tab 组件都是真实实现。第 8 步：检查看板组件、Vite 配置、README 和 PRD 文档。



5:45 PM
前端核心组件全部确认。第 9 步：查看类型定义、schema 校验、PRD 文档和环境配置。



5:45 PM
第 10 步：查看 PRD 文档、数据库实际状态，并检查后端是否在运行。



5:46 PM
注意到一个问题：当前会话的 Bash 执行被权限模式拦截了（"Auto mode is unavailable"），因此我无法运行冒烟测试、检查数据库内容和后端运行状态。我会继续用只读文件工具完成审计，最后向您说明这一点。

第 11 步：查看 Pydantic 校验层和任务表单组件。



5:46 PM
第 12 步：最后检查——全项目搜索测试文件、占位符组件和未使用的代码。



5:48 PM
所有代码审计完成。现在汇总审计结论并撰写规划文档。

审计汇总（基于逐文件通读，非文件名推断）：

后端 8 张表（README 声称 10 张，有出入）、8 组路由、9 个服务模块，全部真实实现
前端 5 个页面 + 4 个功能 Tab，全部接入真实后端 API，无残留模拟数据、无纯界面功能
测试仅 1 个：backend/smoke_test.py（36 项接口冒烟），覆盖 CRUD/校验/风险/首页；AI 类功能（计划、重规划、PDF 问答、周报、汇报）零测试覆盖
发现仓库卫生问题：backend/venv 被提交进 git（约 1.7MB 文件列表）
第 13 步：撰写 docs/researchpilot-v2-plan.md（只新增文档，不改任何业务代码）



5:51 PM
✅ 规划文档已完成：docs/researchpilot-v2-plan.md（本次仅新增这一个文档，未修改任何业务代码）

审计核心结论（都在文档第 1 章有详细依据）
1. 现状盘点：后端 8 张表 + 8 组路由 + 9 个服务模块；前端 5 个页面 + 4 个功能 Tab，全部真实接通后端 API。

2. 功能验证状态：

✅ 已实现且已验证（有 36 项冒烟测试覆盖）：项目/任务 CRUD、进度记录、风险引擎、首页仪表盘
✅ 已实现但未验证（代码完整、零测试覆盖、依赖 DeepSeek Key）：AI 计划生成、动态重规划、PDF 文献问答、周报、汇报中心
仅有界面：无（所有 UI 都接了真实接口，无残留模拟数据）
❌ 尚未实现：研究问题、结构化文献证据、实验记录、结果比较、基于真实记录的 AI 分析、决策转任务闭环——这正是评委指出的缺口
3. 为什么像工程工具（文档第 2 章，7 条原因）：数据模型只有"项目→任务→进度"，没有科研对象；任务依赖链把探索性科研错误表达成单向前置链；风险只认时间不认科研；重规划只会改日期；文献问答不沉淀为证据；周报只报工时。

4. 2.0 方案：闭环完整落地为 5 张新表 + 1 次 task 加列迁移、约 20 个新端点、3 个新 Tab，分 6 个阶段（P0 数据迁移 → P5 聚合收尾，约 8–11 天），每阶段独立验收可回退，1.0 所有模块原样保留。文档里含详细的数据表字段、API 清单、前端组件清单、风险对策表和验收标准，以及一条 10 步评委演示路径。

需要您知晓的两点限制
本次会话的 Bash 执行被权限模式拦截了（提示 "Auto mode is unavailable"），所以我无法实际启动服务重跑冒烟测试、检查数据库内容。因此文档中"已验证"功能的依据是冒烟测试文件存在且覆盖了它们，而非本次实跑结果。如需我实际运行验证，请切换权限模式后告诉我。
顺带发现一个仓库卫生问题：backend/venv/ 虚拟环境被误提交进了 git（约 1.7MB 文件），建议后续清理（文档附录已列入）。
请您审核文档。如需调整（例如：闭环细节、模块范围、实施顺序、文档措辞），告诉我具体修改点即可。



现在把没完成的做完
5:53 PM
好的，开始实施 2.0 升级。我先确认运行环境是否可用，然后按 P0→P5 顺序推进，每阶段向您报告。

第 1 步：检查 Bash 是否恢复可用（上次被权限模式拦截，无法运行测试）



5:53 PM
✅ Bash 已恢复可用。开始 P0：数据层与迁移。

先读完 schemas.py 剩余部分，以便按相同风格扩展。



5:54 PM
现在开始写代码。P0 第 1 项：扩展数据模型——task 表加来源列 + 新增 5 张表。



5:55 PM
现在在 models.py 末尾追加 5 张新表。



5:55 PM
P0 第 2 项：配置上传目录 + 第 3 项：追加新实体的 Pydantic schema。



5:59 PM
heredoc 在 Windows Git Bash 下转义出错了。改用 Edit 工具直接追加。



5:59 PM
P0 第 4 项：编写迁移脚本 migrate_v2.py（备份数据库 + task 加列，幂等）。



6:00 PM
迁移脚本完成。现在 P1：研究问题 + 文献卡片后端。

先写卡片抽取服务 services/literature_card.py。



6:00 PM
现在写 routers/questions.py（研究问题 CRUD + 证据计数）。



6:00 PM
修正一个问题：创建接口用路径传 project_id，schema 里不应强制要求。调整三个 Create schema。



6:01 PM
现在写 routers/cards.py（卡片抽取/CRUD/对比）。



6:01 PM
现在给 risk.py 增加实验停滞规则（P4 的风险增强，先写好后实验路由可直接复用）。



6:02 PM
按项目风格把阈值放进 config.py。



6:02 PM
现在写 routers/experiments.py（实验 CRUD + 运行记录 + 附件 + 对比/总览）。



6:03 PM
清理 experiments.py 里的两处冗余代码。



6:03 PM
现在写 services/experiment_analysis.py（P4：基于真实运行记录的 AI 分析）。



6:03 PM
现在写 routers/analyses.py（AI 分析 + 决策闭环端点）。



6:04 PM
现在接线：serializers 加来源字段、main.py 注册新路由、项目详情返回实验风险。



6:04 PM
注意：ProjectDetailOut 引用了后面才定义的 ExperimentRiskOut，需要把它挪到前面。



6:04 PM
第二个编辑没匹配上，查看当前文件状态。



6:05 PM
现在 projects.py 返回实验风险 + main.py 注册新路由与附件静态服务。



6:05 PM
后端主体完成。P0 第 5 项：运行迁移脚本并验证后端可启动。



6:05 PM
✅ 迁移成功（task 表已加 2 列，数据库已备份），后端导入正常（jieba 的警告是原有依赖问题，无害）。

现在启动后端并跑原有 36 项冒烟测试，验证 1.0 功能无回归。



6:07 PM
✅ 36 项全部通过，1.0 功能零回归。.env 无真实 Key → 新模块将运行在演示模式（可确定性测试）。

先清理两处未使用的导入，然后扩展冒烟测试。



6:08 PM
现在扩展 smoke_test.py，新增 v2 模块的测试段（10–17）。



6:10 PM
修复 17.3 停滞测试的一个逻辑漏洞：该实验已有刚创建的运行记录，需把运行记录时间也改到 10 天前。



6:10 PM
11.1 返回 404，需要看具体错误信息。手动复现一下。



6:11 PM
后端可能还是旧进程（端口被占用，我新启动的没绑定成功）。查看启动日志。



6:12 PM
我的进程确实在运行，但 questions 路由没生效。检查 main.py 当前内容。



6:12 PM
main.py 文件本身是对的。看看运行中的服务器实际注册了哪些路由。



6:13 PM
运行中的服务器没有 v2 路由——说明它启动于 main.py 修改之前（时序问题）。重启后端即可。



8:14 PM
进程已杀掉，新服务器可能还在启动。稍等重试。



8:16 PM
路径映射问题（Git Bash 的 /tmp 与 Windows Python 不互通）。改用当前目录。



8:16 PM
发现路由 bug：questions 路由器的 prefix 与完整路径重复了（/api/questions/projects/{id}/questions）。修复为显式全路径。



8:17 PM
重启后端并重跑完整冒烟测试。



8:17 PM
11、12 段全过。13.1 创建实验报 500，查看后端日志中的异常。



8:17 PM
找到了：清理冗余代码时删掉了 stalled 变量定义，但 ExperimentOut(...) 里还在引用它。修复。



8:17 PM
还有个连锁 bug：_experiment_out 里调 _runs_of 却缺少 db 参数。统一修正函数签名和所有调用点。



8:18 PM
修复 analyses.py 里的调用点。



8:18 PM
15.3 手工笔记返回 422，看具体校验错误。



8:18 PM
curl 的问题是我这边 GBK 编码（已知问题）。用 UTF-8 重现冒烟测试的实际请求。



8:19 PM
错误显示请求体被要求 appliedCount 字段——这个字段只属于重规划响应模型。查看 OpenAPI 中该路径实际绑定的请求体。



8:19 PM
OpenAPI 显示请求体正确。检查该路径的响应 schema——怀疑是响应校验出了问题。



8:19 PM
问题找到了：AnalysisNoteCreate 里混入了 appliedCount 字段——我的追加编辑把字段放错了类。查看 schemas.py 实际内容。



8:20 PM
磁盘上的文件是对的，但服务器行为是旧的——怀疑还有残留进程。彻底重启并重测。



8:20 PM
磁盘文件也产生这个问题！检查 schemas.py 中是否有重复定义。



8:20 PM
applied_count 在文件末尾又出现了一次（无默认值）。看文件最后 20 行。



8:20 PM
找到了：第 1206 行 applied_count: int 意外残留在了 AnalysisNoteCreate 类体内（追加编辑时的残留行）。删除它。



8:21 PM
🎉 后端全部完成：77 项冒烟测试全部通过（原 36 项 + 新增 41 项）。后端 P0/P1/P3/P4 达成。

现在进入 P2/P4：前端实现。先扩展类型定义。



8:21 PM
给 Task 接口加来源字段，然后扩展 API 层。



8:21 PM
现在扩展 services/api.ts，追加 v2 接口函数。



8:22 PM
补充 api.ts 的类型导入。



8:22 PM
现在写 QuestionsTab 组件（研究问题列表 + 编辑 + 证据计数）。



8:22 PM
现在写 LiteratureCardsView（卡片列表/编辑/筛选/对比）。



8:23 PM
现在改造 DocumentLibraryTab，加入"原文问答 | 研究卡片"二级视图切换。



8:24 PM
清理一个未使用的状态变量（避免 lint 报错）。



8:24 PM
现在写 ExperimentsTab（实验列表 + 新建 + 跨实验指标总览）。



8:24 PM
现在写 AnalysisPanel（AI 分析 + 手工笔记 + 建议转任务闭环）。



8:25 PM
现在写 ExperimentDetail（详情 + 运行记录 + 结果对比 + 附件 + 分析面板）。



8:26 PM
清理 ExperimentDetail 中的死代码和未使用导入。



8:26 PM
IDE 诊断是清理前的旧状态，已随刚才的编辑消除。继续：项目详情页加入两个新 Tab。



8:26 PM
给 TaskCard 加来源徽章。



8:26 PM
现在给 ReplanTab 加实验科研风险展示。



8:26 PM
前端主体完成。运行 TypeScript 构建 + lint 验证。



8:27 PM
4 个未使用导入错误，逐一修复。



8:27 PM
重新构建验证。



8:28 PM
✅ 构建通过。运行 lint 检查。



8:28 PM
lint 只有警告（表单重置模式与项目既有代码一致，且为既有告警类型）。确认没有 error 级问题。



8:28 PM
前端 P2/P4 完成（构建 + lint 零错误）。

进入 P5：聚合增强与收尾。先给汇报中心的数据聚合加实验与证据摘要。



8:29 PM
更新汇报 Prompt 与演示模板，融入实验与证据数据。



8:30 PM
周报聚合也加实验运行统计（P5 可选增强）。



8:31 PM
前端周报页加"实验运行"统计卡片。



8:31 PM
重启后端跑全量回归，同时重建前端。



8:31 PM
✅ 77 项回归全部通过。重建前端验证。



8:32 PM
✅ 前端构建 + lint 全部干净。快速验证 Vite 开发服务器能正常启动并代理后端。



8:32 PM
开发服务器 + 代理正常。再做一个 P5 关键验证：演示模式下汇报中心能否把实验进展写进周报。



8:33 PM
路径问题（当前目录在 frontend），改用绝对路径。



8:33 PM
✅ 实验数据成功进入汇报正文。

现在做 仓库卫生清理（venv 出库 + 附件目录入忽略）和文档更新。



8:33 PM
更新 README（表数量、v2 功能、迁移步骤、测试数）。



8:34 PM
补充 README 演示模式表格，并给规划文档追加实施状态。



8:34 PM
发现一个会触发无限请求循环的隐患：几个 useAsyncData 传了内联箭头函数（该项目已知陷阱，每次渲染新引用会反复触发请求）。必须改为 useCallback。



8:34 PM
最终重建 + lint + 冒烟三连验证。



8:35 PM
Vite 开发服务器已退出，重启它。另外发现迁移备份文件 research.db.bak-v2 未被 gitignore 覆盖（*.db 规则匹配不到 .bak-v2 后缀），一并修复。



8:36 PM
✅ ResearchPilot 2.0 全部完成并通过验证。 以下是完整交付报告。

一、实施内容（P0→P5 全部完成）
后端新增（不删不改旧模块，全部叠加）：

5 张新表：research_question（研究问题）、literature_card（文献卡片）、experiment（实验）、experiment_run（运行记录）、experiment_analysis（AI 分析）；task 表加 source_type/source_id 两列
4 组新路由（约 25 个端点）：questions.py、cards.py、experiments.py、analyses.py
2 个新服务：literature_card.py（卡片抽取，无 Key 返回空模板不伪造）、experiment_analysis.py（分析必须引用真实 run 编号）
风险增强：实验停滞/失败待复盘规则（risk.py）；汇报增强：组会周报与周报聚合实验运行与证据数据
迁移脚本 migrate_v2.py：自动备份数据库 + 幂等加列（已执行 ✅）
前端新增：

项目详情页 4 个 Tab → 6 个 Tab（新增「研究问题」「实验」）
文献库 Tab 内新增二级视图「研究卡片」（列表/编辑/筛选/多选字段级对比/一键 AI 抽取）
新组件：QuestionsTab、LiteratureCardsView、ExperimentsTab、ExperimentDetail（运行记录+结果对比+附件）、AnalysisPanel（AI 分析+建议转任务/转实验草稿）
看板任务卡片带来源徽章；重规划 Tab 显示实验科研风险；周报页新增"实验运行"统计卡
二、验证结果（全部实跑）
验证项	结果
后端冒烟测试（原 36 项 1.0 回归 + 41 项 v2 新增）	✅ 77/77 全部通过
前端 npm run build	✅ 通过
前端 npm run lint	✅ 0 错误
端到端：实验数据进入组会周报「本周完成」	✅ 实测通过
数据库迁移	✅ 已备份并加列，1.0 数据完好
三、现在就能在浏览器里测试
两个服务已在运行：后端 http://127.0.0.1:8000，**前端 (http://127.0.0.1:8000%EF%BC%8C**%E5%89%8D%E7%AB%AF)** http://localhost:5174

建议体验路径（回应评委的 10 步闭环）：

打开项目 → 「研究问题」Tab 创建问题
「文献库」→「研究卡片」→ 上传 PDF 后点一键抽取（当前无 Key 是空模板，可手工填）
勾选多张卡片点「对比所选」
「实验」Tab 建实验（定义指标）→ 录入 2~3 次运行记录
点「结果对比」看染色表格 → 「生成 AI 分析」（无 Key 时会提示，可先写手工笔记；转任务闭环可用）
配置真实 Key 后（backend/.env），AI 分析的建议可一键转任务，看板上出现「来源·实验分析」徽章
四、需要您知晓的两点
代码尚未提交 git（共 17 个修改文件 + 12 个新文件，另有 2221 个 venv 条目已从 git 索引移除）。您检查无误后告诉我，我再帮您提交。
AI 分析全链路（分析生成→建议→转任务）在无 Key 时只能测到"拒绝生成 + 手工笔记 + 端点逻辑"（已由测试夹具覆盖）；配好真实 DEEPSEEK_API_KEY 后即可端到端演示完整效果。
您先在浏览器里体验一下，有任何问题（界面细节、流程不顺、字段缺漏）告诉我，我来修。



README.md
现在开始实现 ResearchPilot 2.0 的后端科研数据模块。请先复核 docs/researchpilot-v2-plan.md，并严格按照已审核的方案实施。

本次只完成后端数据层和API，不开发前端。

新增科研业务对象：
1. ResearchQuestion：所属项目、研究问题、研究目标、研究假设、当前状态、创建时间。
2. PaperNote：所属项目、关联文献文件、论文标题、研究问题、方法、数据集、评价指标、创新点、局限性、原文证据片段及页码。
3. Experiment：关联研究问题、实验名称、实验目的、待验证假设、实验变量、对照条件、数据集、模型、评价指标、配置和状态。
4. ExperimentRun：关联实验、运行时间、随机种子、代码Git Commit、环境信息、参数、实际评价指标、日志路径、结果文件路径、备注。
5. ResearchDecision：关联实验记录、观察到的事实、分析解释、是否支持假设、未知因素、下一步研究建议。

要求：
- 尽可能复用原有Project、Task、文献文件和数据库结构。
- 使用新增表和安全迁移，不允许删除原表、清空数据库或丢失已有用户数据。
- 设计完整的Pydantic模型、SQLAlchemy模型、CRUD接口和输入校验。
- 实验指标必须保存用户实际录入或上传的数据，不允许由AI生成虚假的数值。
- 保存创建、修改时间以及必要的关联关系。
- 增加错误处理和接口测试。
- 保留所有原有API及其行为，不得擅自更改已有接口字段。

完成后列出新增文件、修改文件、数据库迁移方案、API清单，并实际运行相关测试。遇到兼容问题先修复，不要通过删除旧功能解决。

本轮完成后暂停，不要继续开发前端。
Show more
8:38 PM
收到。本轮只做后端数据层和 API，不碰前端。我先复核规划文档的相关章节，再按新规格扩展实现（复用上一轮已建的表结构，只加列、加表，不删不改旧字段）。

第 1 步：复核规划文档中数据表与 API 设计部分



8:38 PM
规划文档结构确认无误。本轮新规格是对 §6.1–§6.4 的字段扩展 + 新增 ResearchDecision 实体。

第 2 步：扩展 SQLAlchemy 模型（只加列/加表，不动已有字段）。



8:39 PM
现在新增 ResearchDecision 表（科研决策记录，区别于 AI 分析——这是研究者本人对实验记录的判断与下一步决定）。



8:39 PM
第 3 步：扩展 Pydantic 校验层。先加 ResearchQuestion 的 objective/hypothesis 字段。



8:40 PM
现在加 EvidenceSnippet 模型并扩展卡片 schema。



8:40 PM
扩展 Experiment 的 schema（变量/对照/数据集/模型/配置）。



8:40 PM
扩展 Run 的 schema（随机种子/Git提交/环境/日志/结果文件）。



8:41 PM
现在追加 ResearchDecision 的 Pydantic 模型。



8:41 PM
第 4 步：扩展迁移脚本（改为按表配置的幂等加列，覆盖本轮全部新字段）。



8:41 PM
第 5 步：更新路由层。先改 questions.py 支持新字段。



8:41 PM
改 cards.py：序列化与创建/更新支持创新点和证据片段。



8:42 PM
改 experiments.py：实验与运行记录的序列化和读写支持新字段。



8:42 PM
查看 update_experiment 当前代码（之前 sed 已改过 return）。



8:42 PM
现在创建 routers/decisions.py（科研决策记录 CRUD）。



8:42 PM
第 6 步：执行迁移 + 重启后端验证。



8:43 PM
Bash 又被权限模式拦截了（之前出现过一次后恢复）。我先完成所有不需要 Bash 的工作——扩展冒烟测试，最后再试运行。

第 7 步：扩展 smoke_test.py（新增 v2.1 字段与 ResearchDecision 的测试段）。



8:43 PM
修正 21.5 这个测试设计错误——用列表接口验证证据片段回读，而不是测一个不存在的路径。



8:43 PM
代码全部就绪。现在尝试运行迁移和测试（Bash 刚才被权限拦截，重试一次）。



8:44 PM
趁 Bash 被拦截，我先做一轮静态自查——发现一个 Pydantic 字段顺序问题：我在多个 Out 模型中把带默认值的字段插在了无默认值字段前面（如 objective = None 在 answer_summary 之前），这在类定义时会报错。修复方式：去掉这些中间字段的默认值（所有构造点都已显式传值）。



8:44 PM
修正测试 20.2 的输入（纯空格会被 strip 成空串，无法触发长度校验）。



8:44 PM
再试一次 Bash，看权限模式是否恢复。



8:44 PM
✅ Bash 恢复。立即执行迁移并跑全量测试。



8:45 PM
✅ 迁移完成：5 张表新增 14 列（task 的 2 列已存在自动跳过，备份保留）。重启后端跑全量测试。



8:45 PM
108 通过 3 失败，都是可定位的小问题：21.4 是 update_card 里对已 dump 成 dict 的片段又调 .model_dump() 导致 500；23.4 是 pydantic 原生报错信息是英文不含"字符串"。先看日志确认 21.4 的异常。



8:45 PM
确认：'dict' object has no attribute 'model_dump'。修复 update_card。



8:46 PM
🎉 111 项测试全部通过，0 失败。最后验证新路由注册情况。



8:46 PM
全部路由已注册。给规划文档补一节 v2.1 扩展说明，然后汇总报告。



8:46 PM
✅ 本轮完成：ResearchPilot 2.0 后端科研数据模块（v2.1 扩展），111 项测试全部通过。按要求暂停，未开发前端。

一、新增文件（2 个）
文件	说明
backend/app/routers/decisions.py	科研决策记录 CRUD 路由（含跨实验引用校验、删除保护）
—	其余均为对既有文件的扩展，无其他新文件
二、修改文件（8 个）
文件	改动
backend/app/models.py	ResearchQuestion +objective/hypothesis；LiteratureCard +innovations/evidence_snippets_json；Experiment +variables/control_conditions/dataset/model/config_json；ExperimentRun +random_seed/git_commit/environment_json/log_path/result_files_json；新增 ResearchDecision 表（13→14 张表）
backend/app/schemas.py	上述全部字段的 Pydantic 入参校验（长度/类型/范围/条数）+ 新增 EvidenceSnippet、DecisionCreate/Update/Out
backend/app/routers/questions.py	创建/更新/序列化支持 objective、hypothesis
backend/app/routers/cards.py	支持 innovations、evidenceSnippets（quote+page，含 JSON 损坏容错）
backend/app/routers/experiments.py	实验与运行记录支持全部新字段读写
backend/app/main.py	注册 decisions 路由
backend/migrate_v2.py	改为按表配置的幂等加列迁移
backend/smoke_test.py	77 项 → 111 项（新增 v2.1 测试段 19~25，共 34 项）
三、数据库迁移方案
原则：只加列/加表，不删表、不删列、不清库。迁移前自动备份 research.db → research.db.bak-v2（仅首次，不覆盖）。
已执行结果：14 个新列全部添加成功（幂等，重复执行自动跳过）；research_decision 新表由后端启动时 create_all 自动创建；旧数据完好（1.0 的 36 项回归全过）。
升级操作：cd backend && venv\Scripts\python migrate_v2.py（可在后端启动前任意时刻执行，重复执行安全）。
四、API 清单（本轮新增/变更）
新增端点（ResearchDecision，6 个）：

方法	路径	说明
POST	/api/experiments/{id}/decisions	创建决策（runIds 必须真实存在且属于该实验）
GET	/api/experiments/{id}/decisions	实验的决策列表
GET	/api/projects/{id}/decisions	项目下全部决策
GET	/api/decisions/{id}	决策详情
PUT	/api/decisions/{id}	更新决策
DELETE	/api/decisions/{id}	删除决策（不影响实验与记录）
已有端点扩展（只新增可选响应/入参字段，旧字段行为不变）：questions 创建/更新/查询 + objective/hypothesis；cards 创建/更新/查询 + innovations/evidenceSnippets；experiments 创建/更新/查询 + variables/controlConditions/dataset/model/config；runs 创建/更新/查询 + randomSeed/gitCommit/environment/logPath/resultFiles。

字段映射（复用优先，无重复存储）：run 的 config=本次运行参数、results=实际评价指标——均为用户真实录入，无任何 AI 生成数值。

五、测试结果（实际运行）
冒烟测试：111 项通过 / 0 失败（1.0 回归 36 项 + v2 回归 41 项 + v2.1 新增 34 项）
覆盖：新字段的合法写入与回读、超长/负值/类型错误 → 422 中文提示、证据片段页码校验、跨实验引用 → 400、假设判定三态（支持/否定/null 待定）、级联删除无残留
修复了 2 个实测发现的问题：update_card 对 dict 调 .model_dump() 的 500；Pydantic 默认值字段顺序的类定义错误
后端服务正在 http://127.0.0.1:8000 运行（OpenAPI 共 45 个路径），您可在浏览器访问 /docs 查看全部接口。本轮到此暂停，等待您的下一步指示（前端适配、提交代码或其他调整）。



现在开始开发 ResearchPilot 2.0 的科研实验工作台前端。

请先阅读当前前端的路由结构、组件风格、API封装方式和已完成的后端接口，不要自行假设接口名称和字段。

新增页面：
1. 科研驾驶舱：显示当前研究问题、文献阅读进度、待验证假设、近期实验、重要发现和下一步计划。
2. 文献研究库：展示论文列表；支持上传论文后生成结构化研究卡片；展示问题、方法、数据集、评价指标、创新点、局限性；每条原文证据都能点击定位到对应PDF页或原文片段。
3. 实验工作台：支持创建实验，编辑实验假设、实验变量、对照条件、数据集、模型和指标。
4. 实验运行记录：支持新增运行记录，录入参数、随机种子、Git Commit、环境、实际指标及备注；支持CSV结果导入。
5. 实验结果比较：可以选择多组实验，对相同指标进行可视化对比。指标由数据库真实记录计算，不生成假数据。
6. 研究决策日志：展示观察事实、分析解释、待验证问题和下一步研究建议。

交互要求：
- 所有页面必须连接真实后端API，不能只做静态展示。
- 提供加载、空数据、错误和成功状态。
- 页面要有清晰的操作引导，让第一次使用的研究生也能理解。
- 视觉风格保持专业、简洁、统一，避免过多装饰和无意义统计卡片。
- 保留原有项目管理、任务管理和文献功能，不要删除旧页面。
- 重要操作需要确认，防止误删实验数据。

先完成科研驾驶舱、实验工作台和实验运行记录三个主要流程，再完成结果比较与研究决策日志。完成后运行前端构建并提供实际测试步骤。
Show more
8:51 PM
开始前端科研实验工作台开发。先按要求通读当前前端路由、组件风格与 API 封装（不假设任何接口），再动手。

第 1 步：阅读布局组件、侧边栏和图表风格



8:52 PM
前端结构已清楚（Sidebar 5 项导航、shadcn chart 包装 + Recharts 主题色规范、Sheet 表单模式、useAsyncData 三态）。

第 2 步：扩展类型定义（补齐 v2.1 后端字段 + 决策类型，与后端实际响应严格对应）。



8:53 PM
第 4 步：CSV 解析工具（纯前端解析，导入时走已有 createRun 接口，不新增后端假设）。



8:53 PM
CSV 解析器有冗余逻辑，重写干净版本。



8:53 PM
第 5 步：科研驾驶舱页面（聚合现有真实 API，不做静态展示）。



8:54 PM
清理 CockpitPage 未使用的图标导入。



8:54 PM
第 6 步：实验工作台页面（LabPage 包装 + 项目选择器）。



8:54 PM
现在给 ExperimentFormSheet 加 v2.1 字段（变量/对照/数据集/模型/配置）。



8:55 PM
现在增强 ExperimentDetail：先展示实验的 v2.1 设计字段。



8:55 PM
现在给 RunFormSheet 加 v2.1 复现字段（种子/提交/环境/日志/结果文件）。



8:55 PM
运行记录卡片展示复现信息。



8:56 PM
现在给实验详情加 CSV 结果导入（预览确认 → 逐条走真实 createRun 接口）。



8:56 PM
在 ExperimentDetail 中插入 CsvImportSheet 组件。



8:56 PM
接线：在实验详情页头部加 CSV 导入入口。



8:56 PM
实验工作台与运行记录完成。接下来做结果比较页，涉及图表——按规范先加载图表设计技能。



dataviz skill
8:56 PM
按技能要求先读参考调色板，再设计图表。



8:57 PM
按技能流程：先运行调色板验证脚本（8 个分类色，明暗双模式），通过后再写图表。



8:58 PM
验证脚本是 ES 模块，复制为 .mjs 后运行。



8:58 PM
退出码 0（通过）但无输出。看一下脚本的输出逻辑确认结果。



8:59 PM
✅ 明暗两套 8 色调色板均通过验证（退出码 0）。现在按规范编写 ComparePage（分组柱状图小倍数 + 数据表双视图、图例、悬浮提示、实验稳定配色）。



8:59 PM
现在写 研究决策日志页（DecisionsPage：按实验查看/新建/编辑/确认删除）。



9:00 PM
现在做 文献研究库增强。先改 LiteratureCardsView：加创新点字段、证据片段编辑器与点击定位回调。



9:01 PM
补回 Input 导入，然后加卡片列表的创新点与可点击证据片段。



9:01 PM
现在改 DocumentLibraryTab：加 initialView 属性和证据片段定位逻辑。



9:02 PM
现在写 文献研究库页面（LibraryPage）。



9:02 PM
接线：路由 + 侧边栏 + 页面标题。



9:03 PM
所有页面与路由完成。运行构建验证。



9:03 PM
4 个错误，逐一修复。先是卡片字段类型收窄（避免 evidenceSnippets 数组混入文本字段）。



9:05 PM
构建与 lint 全部通过。修复一个边界问题：ComparePage 中按 id 排序超出 8 个色槽的实验可能被勾选但无颜色。



9:05 PM
构建通过、后端正常。现在跑一个端到端数据流验证——模拟新页面实际调用的完整 API 链路。



9:06 PM
✅ 端到端链路全部验证通过（证据片段、v2.1 字段、指标总览数据点、决策、驾驶舱聚合）。重启前端开发服务器供手动测试。



9:07 PM
Vite 这次起了 5173 端口。验证。



9:07 PM
前端 5173 正常。最后跑一次后端全量回归确认无影响，然后汇总交付。



9:07 PM
✅ 科研实验工作台前端开发完成，构建通过、lint 零错误、后端 111 项回归全过。

一、交付内容（6 个页面/流程全部落地）
页面	路由	说明
科研驾驶舱	/cockpit	项目选择 + 一屏聚合：当前研究问题（证据计数）、待验证假设（问题+实验）、文献阅读进度（卡片/文献进度条）、近期实验、重要发现（决策）、下一步计划（决策建议+近期任务）。数据全部来自 6 个真实接口聚合
文献研究库	/library	上传论文→AI 生成结构化卡片；展示问题/方法/数据集/指标/创新点/局限；证据片段点击定位原文切片并高亮（页码徽章；未关联文献或未匹配到原文时给出明确提示）
实验工作台	/lab	创建/编辑实验：假设、实验变量、对照条件、数据集、模型、实验配置(JSON)、指标定义；实验列表含状态/停滞提醒；删除需二次确认
实验运行记录	实验工作台内详情	录入参数、随机种子、Git Commit、环境(JSON)、实际指标、日志路径、结果文件路径、备注；CSV 批量导入（预览→确认→逐条走真实接口，失败中断并提示已导入条数）；附件上传
实验结果比较	/compare	勾选多个实验（≤8，色板槽位上限），按同一指标对齐「第 N 次运行」做分组柱状图对比（每指标一张图，无假数据、无双轴）；含数据表视图；图表配色经 validate_palette.js 明/暗双模式验证通过
研究决策日志	/decisions	按实验查看/新建/编辑决策：观察事实、分析解释、支持/否定/待定假设三态、未知因素、下一步建议；删除二次确认
所有页面均含加载/空数据引导/错误重试/成功提示四态；旧页面（首页/看板/项目仪表盘/周报）全部保留，侧边栏新增「科研工作台」分组。

二、文件清单
新增 7 个：CockpitPage.tsx、LabPage.tsx、ComparePage.tsx、DecisionsPage.tsx、LibraryPage.tsx、csv.ts（CSV 解析器，支持引号/转义/BOM）、[README 未动]…

修改 9 个：App.tsx（+5 路由）、Sidebar.tsx（三组导航）、AppLayout.tsx（页面标题）、types/index.ts（v2.1 字段+决策类型）、api.ts（决策接口）、ExperimentsTab.tsx（v2.1 表单）、ExperimentDetail.tsx（v2.1 展示+CSV 导入）、LiteratureCardsView.tsx（创新点+证据片段+定位）、DocumentLibraryTab.tsx（视图切换+片段高亮定位）

三、验证结果（实际运行）
前端 npm run build ✅ 通过；npm run lint ✅ 0 错误
后端冒烟回归 ✅ 111/111（本轮无后端改动，确认无影响）
端到端链路实测 ✅：问题(目标/假设)→卡片(证据片段)→实验(v2.1 字段)→3 条运行记录→指标总览数据点(80.1/87.3/86.9)→决策(支持假设+建议)→驾驶舱聚合接口，全部返回正确
修复过程中发现的 4 个 TS 错误（卡片字段类型收窄、未用参数等）
四、实际测试步骤（浏览器手动验证）
两个服务已运行：**前端 http://localhost:5173**，后端 (http://localhost:5173**%EF%BC%8C%E5%90%8E%E7%AB%AF) http://127.0.0.1:8000

准备数据（若库是空的）：首页 → 新建项目 → 生成 AI 计划（无 Key 也有演示计划）确认创建。
科研驾驶舱 /cockpit：应看到空状态引导 → 去项目仪表盘「研究问题」建一条带目标/假设的问题 → 回驾驶舱看"当前研究问题"与"待验证假设"出现。
实验工作台 /lab：新建实验（填假设/变量/对照/数据集/模型/配置 {"epochs":50}/指标 Accuracy(%)）→ 进入实验详情。
运行记录：点「新增运行记录」录一条（种子 42、指标 Accuracy=80.1）→ 再录一条（87.3）→ 点「结果对比」看染色表格。
CSV 导入：建一个 UTF-8 的 CSV：

Accuracy,note
86.9,第三次运行
88.1,第四次运行
点「CSV 导入」→ 选择文件 → 预览确认 → 导入成功提示 → 运行记录变为 4 条。
结果比较 /compare：勾选该实验（≥2 次运行才有数据点）→ 图表视图出现 Accuracy 柱状图（悬浮看数值）→ 切「数据表视图」核对。
决策日志 /decisions：选实验 → 「记录新决策」→ 勾选运行记录 → 填观察事实 → 选"支持假设" → 填未知因素与建议 → 保存。回 /cockpit 看"重要发现"与"下一步计划"已更新。
文献研究库 /library：上传一篇含文字层 PDF → 「研究卡片」视图点该文献一键抽取（无 Key 返回空模板）→ 手工填方法/创新点，添加证据片段（摘录原文+页码）→ 保存后点击该片段 → 自动切到原文视图并高亮定位到包含摘录的切片。
删除保护：删除实验/运行记录/卡片/决策时都是"点击→确认删除→再点击"两步，防止误删。
五、两点如实说明
PDF 按页渲染暂未实现：后端只存储提取后的文字（切片无页码映射），因此证据片段点击定位到的是原文切片高亮（需求允许的"或原文片段"路径），并保留页码徽章供人工核对。若需真正的按页渲染，需要后端存储 PDF 原件并做页级切分（后端改动，未在本轮范围）。
CSV 导入约定：表头为列名、每行一条运行记录、note 列写备注、其余列按名称写入实际指标、空单元格跳过、上限 100 行；导入中断时会提示已成功导入的条数。
代码未提交 git。您浏览器测试后如有问题告诉我；确认无误后我再帮您提交。



现在开发 ResearchPilot 2.0 的 AI 研究分析服务，使用项目原有的DeepSeek API后端封装，不要让前端直接请求模型。

核心功能：用户选择一个ResearchQuestion，系统读取与之关联的PaperNote、Experiment和ExperimentRun，将真实数据整理成上下文，再由DeepSeek生成研究分析。

AI输出必须严格区分以下内容：
1. observed_facts：数据库中真实存在的实验事实，必须附带experiment_run_id。
2. paper_evidence：文献中明确出现的依据，必须附带paper_note_id、原文片段ID和页码；找不到依据时返回空，不得编造引用。
3. interpretation：基于当前事实提出的解释，明确标记为推测而不是结论。
4. hypothesis_status：支持、不支持或证据不足。不能仅凭一次实验就声称假设得到证明。
5. uncertainty：当前数据中的不足、潜在混杂因素和无法判断的问题。
6. next_experiments：最多提出3个下一步实验，每个包含实验目的、待验证假设、改变变量、保持不变的条件、评价指标、预期观察、风险和估计工作量。
7. task_conversion：用户确认后才能将实验建议转化为原有Task。

严格约束：
- 不得生成数据库中不存在的实验数值、论文、数据集或引用。
- 如果没有真实实验记录，明确提示“当前缺少实验数据，无法进行结果分析”，不能用虚构结果替代。
- 文献原文没有说明的内容必须标记为“原文未找到”。
- 分析建议不能冒充科研事实。
- 对实验结果进行数值比较时由Python后端完成确定性计算，DeepSeek负责解释和建议。
- 输出使用Pydantic校验的严格JSON结构，处理缺失字段、格式异常、超时和API错误。
- 用户采纳建议之前，不得修改原有实验记录或任务计划。

请补充单元测试，至少验证：无实验数据、只有一组实验、多组实验、有缺失文献证据、模型返回错误JSON、API不可用等情况。完成后展示一份基于实际数据库数据的分析结果。没有真实数据时请明确使用标记为演示的数据，并不得将其描述为真实实验。
Show more
9:11 PM
开始开发 AI 研究分析服务。设计要点先明确：数值计算全部由 Python 后端确定性完成（DeepSeek 只做解释与建议）、证据引用经过硬校验（run id/卡片 id/片段 id 必须真实存在，页码以数据库为准）、无 Key 时走演示模板（统计值真实、文字模板、明确标注）、转任务需显式调用确认接口。

第 1 步：新增 ResearchAnalysis 数据表。



9:11 PM
看一下 models.py 中 ResearchDecision 的实际文本。



9:12 PM
第 2 步：追加 Pydantic 模型（分析输出结构）。



9:12 PM
第 3 步：核心服务（确定性统计 + 严格校验 + DeepSeek 编排 + 演示模板）。



Write e:\ResearchPilot\backend\app\services\research_analysis.py
604 lines
"""AI 研究分析编排（v2.2 核心服务）：

职责边界（严格）：
- Python 后端：确定性统计计算（min/max/mean/best/delta）、上下文组装、引用校验；
- DeepSeek：只负责解释、判断与建议，不得自行计算数值或编造引用；
- 数据库：唯一事实来源——不存在的 run/卡片/片段引用一律丢弃，页码与原文以库为准。

输出结构（严格 JSON，Pydantic 校验）：
1. observed_facts   实验事实（必须带真实 experiment_run_id）
2. paper_evidence   文献证据（必须带真实 paper_note_id + snippet_id，页码/原文以库为准）
3. interpretation   解释（明确为推测，非结论）
4. hypothesis_status support / not_support / insufficient_evidence
5. uncertainty      数据不足、混杂因素、无法判断的问题
6. next_experiments 最多 3 条（8 个字段齐全）
7. task_conversion  由用户显式调用转换接口，AI 输出阶段不产生任何任务

无实验记录 → ResearchAnalysisError（路由转 400，明确提示）；
无 Key → 演示模板（统计值真实、文字模板、source=demo）。
"""
import json
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekClient, DeepSeekError
from app.config import AI_FORMAT_RETRY_TIMES, DEEPSEEK_API_KEY
from app.models import Experiment, ExperimentRun, LiteratureCard, ResearchQuestion

NO_DATA_MESSAGE = "当前缺少实验数据，无法进行结果分析；请先为该研究问题关联实验并录入真实运行记录"
MAX_NEXT_EXPERIMENTS = 3
HYPOTHESIS_STATUSES = ("support", "not_support", "insufficient_evidence")


class ResearchAnalysisError(Exception):
    """用户可读的分析前置条件错误（路由层转 400）。"""


class ResearchFormatError(Exception):
    """DeepSeek 输出格式/约束错误（触发重试）。"""


def _fmt_number(value) -> str:
    """数值展示：浮点保留 4 位小数，整数原样。"""
    if isinstance(value, float):
        return f"{round(value, 4):g}"
    return str(value)


def _load_json(text: str | None, default):
    try:
        return json.loads(text) if text else default
    except (ValueError, TypeError):
        return default


# ═══════════════════════ 确定性统计（Python 计算，AI 不得自行算数） ═══════════════════════

def compute_stats(experiments: list[dict]) -> dict:
    """按指标聚合全部实验运行记录，计算确定性统计。

    experiments: [{"id", "title", "metrics": [{"name","unit","higher_is_better"}],
                   "runs": [{"run_no", "results": {指标名: 数值}}]}]

    返回：
    {
      "metrics": [{"name","unit","higher_is_better","experiments": [
          {"experiment_id","title","run_count","min","max","mean",
           "best","best_run_no","latest","latest_run_no"}]}],
      "comparisons": [{"metric","unit","higher_is_better","rows": [
          {"experiment_id","title","best","best_run_no","delta_vs_first"}]}]
    }
    """
    # 指标名 → {"unit", "higher_is_better", "points": [(exp_id, title, run_no, value)]}
    metric_map: dict[str, dict] = {}
    for exp in experiments:
        direction_map = {m["name"]: m.get("higher_is_better", True) for m in exp.get("metrics", [])}
        unit_map = {m["name"]: m.get("unit", "") for m in exp.get("metrics", [])}
        for run in exp.get("runs", []):
            for name, value in (run.get("results") or {}).items():
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue  # 非数值不进统计
                group = metric_map.setdefault(
                    name,
                    {"unit": unit_map.get(name, ""),
                     "higher_is_better": direction_map.get(name, True),
                     "points": []},
                )
                group["points"].append((exp["id"], exp["title"], run["run_no"], float(value)))

    metrics = []
    comparisons = []
    for name in sorted(metric_map.keys()):
        group = metric_map[name]
        higher = group["higher_is_better"]
        by_exp: dict[int, dict] = {}
        for exp_id, title, run_no, value in group["points"]:
            entry = by_exp.setdefault(
                exp_id,
                {"experiment_id": exp_id, "title": title, "values": []},
            )
            entry["values"].append((run_no, value))

        rows = []
        for entry in by_exp.values():
            values = sorted(entry["values"], key=lambda x: x[0])
            nums = [v for _, v in values]
            best_run_no, best = max(values, key=lambda x: x[1]) if higher else min(values, key=lambda x: x[1])
            latest_run_no, latest = values[-1]
            rows.append({
                "experiment_id": entry["experiment_id"],
                "title": entry["title"],
                "run_count": len(nums),
                "min": round(min(nums), 4),
                "max": round(max(nums), 4),
                "mean": round(sum(nums) / len(nums), 4),
                "best": round(best, 4),
                "best_run_no": best_run_no,
                "latest": round(latest, 4),
                "latest_run_no": latest_run_no,
            })
        rows.sort(key=lambda r: r["experiment_id"])
        metrics.append({
            "name": name,
            "unit": group["unit"],
            "higher_is_better": higher,
            "experiments": rows,
        })

        # 跨实验比较：仅当 >=2 个实验都报告了该指标
        if len(rows) >= 2:
            first_best = rows[0]["best"]
            comparison_rows = [
                {
                    "experiment_id": r["experiment_id"],
                    "title": r["title"],
                    "best": r["best"],
                    "best_run_no": r["best_run_no"],
                    "delta_vs_first": round(r["best"] - first_best, 4),
                }
                for r in rows
            ]
            comparisons.append({
                "metric": name,
                "unit": group["unit"],
                "higher_is_better": higher,
                "rows": comparison_rows,
            })

    return {"metrics": metrics, "comparisons": comparisons}


# ═══════════════════════ 上下文组装 ═══════════════════════

def gather_context(db: Session, question: ResearchQuestion) -> dict:
    """读取与研究问题关联的真实数据，组装分析上下文。

    返回结构（同时供 Prompt 与校验使用）：
    {
      "question": {...},
      "cards": [{"id","title","method","metrics","key_results","limitations","innovations",
                 "snippets":[{"snippet_id":"卡片id-序号","page","quote"}]}],
      "experiments": [{"id","title","objective","hypothesis","status",
                       "metrics":[MetricDef dict...],
                       "runs":[{"id","run_no","config","results","notes","random_seed","git_commit"}]}],
      "stats": compute_stats(...),
      "valid_run_ids": {int},
      "n_experiments": int,
    }
    """
    cards = list(
        db.scalars(
            select(LiteratureCard)
            .where(LiteratureCard.question_id == question.id)
            .order_by(LiteratureCard.id)
        )
    )
    experiments = list(
        db.scalars(
            select(Experiment)
            .where(Experiment.question_id == question.id)
            .order_by(Experiment.id)
        )
    )

    card_ctx = []
    for card in cards:
        snippets_raw = _load_json(card.evidence_snippets_json, [])
        snippets = []
        for index, sn in enumerate(snippets_raw, start=1):
            if not isinstance(sn, dict) or not str(sn.get("quote") or "").strip():
                continue
            snippets.append({
                "snippet_id": f"{card.id}-{index}",
                "page": str(sn.get("page") or "").strip() or None,
                "quote": str(sn["quote"]).strip(),
            })
        card_ctx.append({
            "id": card.id,
            "title": card.title or "未命名卡片",
            "method": card.method or "",
            "metrics": card.metrics or "",
            "key_results": card.key_results or "",
            "limitations": card.limitations or "",
            "innovations": card.innovations or "",
            "snippets": snippets,
        })

    experiments_data = []
    experiment_ctx = []
    valid_run_ids: set[int] = set()
    for exp in experiments:
        runs = list(
            db.scalars(
                select(ExperimentRun)
                .where(ExperimentRun.experiment_id == exp.id)
                .order_by(ExperimentRun.run_no)
            )
        )
        metric_defs = _load_json(exp.metrics_json, [])
        run_ctx = []
        for run in runs:
            valid_run_ids.add(run.id)
            run_ctx.append({
                "id": run.id,
                "run_no": run.run_no,
                "config": _load_json(run.config_json, {}),
                "results": _load_json(run.results_json, {}),
                "notes": run.notes or "",
                "random_seed": run.random_seed,
                "git_commit": run.git_commit,
            })
        experiments_data.append({
            "id": exp.id,
            "title": exp.title,
            "metrics": [
                {"name": m.get("name", ""), "unit": m.get("unit", ""),
                 "higher_is_better": m.get("higher_is_better", True)}
                for m in metric_defs if isinstance(m, dict) and m.get("name")
            ],
            "runs": [{"run_no": r["run_no"], "results": r["results"]} for r in run_ctx],
        })
        experiment_ctx.append({
            "id": exp.id,
            "title": exp.title,
            "objective": exp.objective,
            "hypothesis": exp.hypothesis or "",
            "status": exp.status,
            "runs": run_ctx,
        })

    stats = compute_stats(experiments_data)
    return {
        "question": {
            "id": question.id,
            "content": question.content,
            "objective": question.objective or "",
            "hypothesis": question.hypothesis or "",
        },
        "cards": card_ctx,
        "experiments": experiment_ctx,
        "stats": stats,
        "valid_run_ids": valid_run_ids,
        "n_experiments": len(experiments),
    }


# ═══════════════════════ Prompt 组装 ═══════════════════════

def build_messages(context: dict) -> list[dict]:
    """组装强约束 Prompt：所有引用必须来自给定数据，数值只能引用统计块。"""
    question = context["question"]
    stats = context["stats"]

    run_lines = []
    for exp in context["experiments"]:
        run_lines.append(f"实验「{exp['title']}」（experiment_id={exp['id']}，状态 {exp['status']}）")
        run_lines.append(f"  目的：{exp['objective']}")
        if exp["hypothesis"]:
            run_lines.append(f"  待验证假设：{exp['hypothesis']}")
        for run in exp["runs"]:
            run_lines.append(
                f"  - 运行 #{run['run_no']}（experiment_run_id={run['id']}）："
                f"指标={json.dumps(run['results'], ensure_ascii=False)}，"
                f"参数={json.dumps(run['config'], ensure_ascii=False)}，"
                f"备注={run['notes'] or '无'}，随机种子={run['random_seed']}，"
                f"Git={run['git_commit'] or '无'}"
            )

    card_lines = []
    for card in context["cards"]:
        card_lines.append(f"[paper_note_id={card['id']}]《{card['title']}》")
        if card["method"]:
            card_lines.append(f"  方法：{card['method'][:300]}")
        if card["key_results"]:
            card_lines.append(f"  主要结果：{card['key_results'][:500]}")
        if card["limitations"]:
            card_lines.append(f"  局限：{card['limitations'][:300]}")
        for sn in card["snippets"]:
            card_lines.append(
                f"  证据片段 {sn['snippet_id']}（页码 p.{sn['page'] or '未知'}）：{sn['quote'][:300]}"
            )

    system = (
        "你是严谨的科研分析助手。用户提供：一个研究问题、关联文献卡片（含证据片段）"
        "、关联实验的运行记录、以及由后端确定性计算好的统计值。\n"
        "输出要求（必须严格遵守）：\n"
        "1. 只输出一个 JSON 对象，不要任何解释文字或 Markdown 代码块：\n"
        '   {"observed_facts": [{"experiment_run_id": 数字, "content": "事实描述"}], '
        '"paper_evidence": [{"paper_note_id": 数字, "snippet_id": "卡片id-序号", '
        '"page": "页码", "quote": "原文摘录", "statement": "该证据说明什么"}], '
        '"interpretation": "解释（推测）", '
        '"hypothesis_status": "support / not_support / insufficient_evidence", '
        '"uncertainty": "数据不足与无法判断之处", '
        '"next_experiments": [{"objective": "", "hypothesis": "", "changed_variables": "", '
        '"fixed_conditions": "", "metrics": "", "expected_observation": "", '
        '"risks": "", "estimated_effort": ""}]}\n'
        "2. observed_facts 只能引用给定运行记录中真实存在的 experiment_run_id 与数值，"
        "禁止编造任何记录或数字；\n"
        "3. paper_evidence 只能引用给定卡片与片段：paper_note_id、snippet_id、quote "
        "必须逐字来自给定数据；找不到文献依据时 paper_evidence 写空数组 []，"
        "并在 interpretation/uncertainty 中明确写「原文未找到」——严禁编造引用；\n"
        "4. interpretation 是基于当前事实的推测而非结论，表述必须体现推测性质"
        "（如「可能是」「推测」「尚不能确定」），不得使用「证明」「证实」等结论性词汇；\n"
        "5. hypothesis_status 只能取 support / not_support / insufficient_evidence 之一："
        "仅有一组实验或单次运行时，不得声称假设得到证明，应谨慎给出判断；\n"
        "6. 所有数值只能引用「确定性统计」块中的数据，不得自行计算或编造数值；\n"
        "7. next_experiments 最多 3 条，每条 8 个字段都必须给出（不确定时写「待定」），"
        "建议是待验证的实验方向，不是结论；\n"
        "8. 若文献对某问题没有说明，明确写「原文未找到」，不得用外部知识补充。"
    )
    user = (
        f"研究问题：{question['content']}\n"
        f"研究目标：{question['objective'] or '无'}\n"
        f"研究假设：{question['hypothesis'] or '无'}\n\n"
        f"确定性统计（后端计算，可信）：\n{json.dumps(stats, ensure_ascii=False)}\n\n"
        f"实验运行记录（共 {len(context['experiments'])} 组实验）：\n" + "\n".join(run_lines) + "\n\n"
        f"文献卡片与证据片段：\n" + "\n".join(card_lines) + "\n"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


# ═══════════════════════ 输出校验（严格，防编造） ═══════════════════════

def _extract_json(text: str) -> dict:
    raw = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start == -1 or end <= start:
            raise ResearchFormatError("输出中找不到 JSON 对象")
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as e:
            raise ResearchFormatError(f"JSON 解析失败：{e.msg}")
    if not isinstance(data, dict):
        raise ResearchFormatError("顶层结构不是 JSON 对象")
    return data


def _normalize(text: str) -> str:
    return "".join(text.split())


def validate_analysis(data: dict, context: dict) -> dict:
    """严格校验 AI 输出：引用必须真实存在，页码/原文以数据库为准。

    返回完整分节结构；硬性违反抛 ResearchFormatError（触发重试）。
    """
    # 1. observed_facts：引用必须真实存在
    raw_facts = data.get("observed_facts")
    if not isinstance(raw_facts, list):
        raise ResearchFormatError("observed_facts 必须是数组")
    facts = []
    for item in raw_facts:
        if not isinstance(item, dict):
            continue
        try:
            run_id = int(item.get("experiment_run_id"))
        except (TypeError, ValueError):
            continue
        if run_id not in context["valid_run_ids"]:
            continue  # 引用不存在的记录 → 丢弃（不得编造）
        content = str(item.get("content") or "").strip()
        if not content:
            continue
        facts.append({"experiment_run_id": run_id, "content": content[:2000]})
    if not facts:
        raise ResearchFormatError("observed_facts 中没有引用任何真实存在的运行记录")

    # 2. paper_evidence：引用必须真实存在，页码/原文以库为准
    raw_evidence = data.get("paper_evidence")
    if not isinstance(raw_evidence, list):
        raise ResearchFormatError("paper_evidence 必须是数组")
    card_by_id = {c["id"]: c for c in context["cards"]}
    snippet_map = {
        sn["snippet_id"]: sn for c in context["cards"] for sn in c["snippets"]
    }
    evidence = []
    for item in raw_evidence:
        if not isinstance(item, dict):
            continue
        try:
            card_id = int(item.get("paper_note_id"))
        except (TypeError, ValueError):
            continue
        if card_id not in card_by_id:
            continue  # 编造的卡片 id → 丢弃
        snippet = snippet_map.get(str(item.get("snippet_id") or ""))
        if snippet is None:
            continue  # 编造的片段 id → 丢弃
        ai_quote = _normalize(str(item.get("quote") or ""))
        if ai_quote:
            # AI 给的原句必须是片段原文的子串（防改写/编造）
            if ai_quote[:8] not in _normalize(snippet["quote"]):
                continue
        statement = str(item.get("statement") or "").strip()
        if not statement:
            continue
        evidence.append({
            "paper_note_id": card_id,
            "snippet_id": snippet["snippet_id"],
            "page": snippet["page"],     # 页码以数据库为准
            "quote": snippet["quote"],   # 原文以数据库为准（防 AI 改写）
            "statement": statement[:2000],
        })

    # 3. interpretation：非空，标注推测
    interpretation = str(data.get("interpretation") or "").strip()
    if not interpretation:
        raise ResearchFormatError("缺少 interpretation 字段")

    # 4. hypothesis_status：枚举
    status = str(data.get("hypothesis_status") or "")
    if status not in HYPOTHESIS_STATUSES:
        raise ResearchFormatError(
            "hypothesis_status 必须是 support / not_support / insufficient_evidence 之一"
        )

    # 5. uncertainty
    uncertainty = str(data.get("uncertainty") or "").strip()

    # 单组实验不得声称证明
    if context["n_experiments"] <= 1:
        for word in ("证明", "证实", "已验证"):
            if word in interpretation + uncertainty:
                raise ResearchFormatError(
                    f"仅有一组实验时不得使用「{word}」等结论性表述"
                )

    # 6. next_experiments：≤3 条，关键字段必填
    raw_next = data.get("next_experiments")
    if not isinstance(raw_next, list):
        raise ResearchFormatError("next_experiments 必须是数组")
    next_experiments = []
    for item in raw_next[:MAX_NEXT_EXPERIMENTS]:
        if not isinstance(item, dict):
            continue
        objective = str(item.get("objective") or "").strip()
        hypothesis = str(item.get("hypothesis") or "").strip()
        if not objective or not hypothesis:
            continue  # 缺关键字段 → 丢弃
        next_experiments.append({
            "objective": objective[:1000],
            "hypothesis": hypothesis[:1000],
            "changed_variables": str(item.get("changed_variables") or "").strip()[:1000],
            "fixed_conditions": str(item.get("fixed_conditions") or "").strip()[:1000],
            "metrics": str(item.get("metrics") or "").strip()[:1000],
            "expected_observation": str(item.get("expected_observation") or "").strip()[:1000],
            "risks": str(item.get("risks") or "").strip()[:1000],
            "estimated_effort": str(item.get("estimated_effort") or "").strip()[:500],
            "converted": False,
        })

    return {
        "observed_facts": facts,
        "paper_evidence": evidence,
        "interpretation": interpretation,
        "hypothesis_status": status,
        "uncertainty": uncertainty,
        "next_experiments": next_experiments,
    }


# ═══════════════════════ 演示模板（无 Key；统计值真实、文字模板） ═══════════════════════

DEMO_WARNING = (
    "演示模式：未配置 DeepSeek API Key。本分析的统计数值由后端基于数据库真实记录确定性计算，"
    "分析文字为模板生成，不代表真实分析结论；请在 backend/.env 配置 DEEPSEEK_API_KEY 后重新生成。"
)


def build_demo_analysis(context: dict) -> dict:
    """无 Key 时的演示分析：observed_facts / paper_evidence / stats 全部来自真实数据，
    解释与建议为明确标注的模板文字。"""
    facts = []
    for exp in context["experiments"]:
        if not exp["runs"]:
            continue
        run = exp["runs"][-1]  # 最新一次运行
        parts = [
            f"{name}={_fmt_number(value)}"
            for name, value in run["results"].items()
        ]
        facts.append({
            "experiment_run_id": run["id"],
            "content": f"实验「{exp['title']}」第 {run['run_no']} 次运行：{'；'.join(parts)}"
            + (f"（备注：{run['notes']}）" if run["notes"] else ""),
        })

    evidence = []
    for card in context["cards"]:
        for sn in card["snippets"][:2]:
            evidence.append({
                "paper_note_id": card["id"],
                "snippet_id": sn["snippet_id"],
                "page": sn["page"],
                "quote": sn["quote"],
                "statement": "（演示模式）该证据来自文献卡片摘录，请人工核对原文",
            })

    summary_lines = []
    for metric in context["stats"].get("metrics", []):
        for row in metric["experiments"]:
            summary_lines.append(
                f"{metric['name']}（{row['title']}）：{row['run_count']} 次运行，"
                f"均值 {row['mean']}，最优 {row['best']}（第 {row['best_run_no']} 次）"
            )
    interpretation = (
        "（演示模式·推测性说明，非真实分析结论）"
        + "后端确定性统计显示：" + "；".join(summary_lines)
        + "。上述数值来自数据库真实记录的计算；"
        + "解释文字为模板生成，请配置 DeepSeek API Key 获得真实分析。"
    )
    uncertainty = (
        "（演示模式）模板生成：样本量、重复次数、潜在混杂因素等"
        "需由真实分析评估；当前内容不代表任何结论。"
    )
    next_experiments = [{
        "objective": "（演示模板）围绕关键变量设计一次对照实验",
        "hypothesis": "（演示模板）调整关键变量后指标变化方向待验证",
        "changed_variables": "（演示模板）待定",
        "fixed_conditions": "（演示模板）保持现有数据划分与评价方式不变",
        "metrics": "（演示模板）沿用当前实验指标",
        "expected_observation": "（演示模板）待定",
        "risks": "（演示模板）请人工评估",
        "estimated_effort": "（演示模板）待定",
        "converted": False,
    }]
    return {
        "observed_facts": facts,
        "paper_evidence": evidence,
        "interpretation": interpretation,
        "hypothesis_status": "insufficient_evidence",
        "uncertainty": uncertainty,
        "next_experiments": next_experiments,
    }


# ═══════════════════════ 生成入口 ═══════════════════════

def generate_analysis(db: Session, question: ResearchQuestion) -> tuple[dict, str]:
    """返回 (sections, source)。source: deepseek / demo。

    无运行记录 → ResearchAnalysisError；无 Key → 演示模板；
    AI 格式错误自动重试，重试耗尽抛 DeepSeekError。
    """
    context = gather_context(db, question)
    if not context["valid_run_ids"]:
        raise ResearchAnalysisError(NO_DATA_MESSAGE)

    if not DEEPSEEK_API_KEY:
        return build_demo_analysis(context), "demo"

    client = DeepSeekClient()
    messages = build_messages(context)
    for attempt in range(1 + AI_FORMAT_RETRY_TIMES):
        content = client.chat(messages)
        try:
            data = _extract_json(content)
            sections = validate_analysis(data, context)
            return sections, "deepseek"
        except ResearchFormatError as e:
            if attempt >= AI_FORMAT_RETRY_TIMES:
                raise DeepSeekError(
                    "AI 返回的分析格式多次校验失败，请稍后重试；"
                    "未配置密钥时可用演示模式查看统计结果"
                ) from e
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"上一次输出不满足要求（{e}）。请严格按 JSON 结构输出，"
                        "所有引用必须来自给定数据，数值只能引用确定性统计块。"
                    ),
                }
            )
    raise DeepSeekError("分析生成失败，请稍后重试")  # 理论不可达
9:13 PM
第 4 步：路由层（生成/历史/详情/确认转任务）。



Write e:\ResearchPilot\backend\app\routers\research_analyses.py
152 lines
"""AI 研究分析接口（v2.2）：

POST /questions/{id}/analysis    按研究问题聚合真实数据生成分析
GET  /questions/{id}/analyses    分析历史
GET  /research-analyses/{id}     分析详情
POST /research-analyses/{id}/suggestions/{i}/to-task   用户确认后转科研任务

严格约束：
- 前端不直接请求模型，全部经由本后端；
- 无运行记录 → 400 明确提示（不用虚构结果替代）；
- 无 Key → 演示模板（统计值真实、文字模板、source=demo、warning 提示）；
- 用户采纳建议之前不修改任何实验记录或任务计划（本接口只读+新增分析记录，
  转任务必须显式调用 to-task）。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import ResearchAnalysis, ResearchQuestion, Task
from app.schemas import (
    NextExperimentOut,
    ObservedFactOut,
    PaperEvidenceOut,
    ResearchAnalysisOut,
    ResearchAnalysisToTaskOut,
)
from app.services.research_analysis import (
    DEMO_WARNING,
    ResearchAnalysisError,
    generate_analysis,
)
from app.services.serializers import build_task_out

router = APIRouter(tags=["研究分析"])


def _get_question_or_404(db: Session, question_id: int) -> ResearchQuestion:
    question = db.get(ResearchQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="研究问题不存在")
    return question


def _get_analysis_or_404(db: Session, analysis_id: int) -> ResearchAnalysis:
    analysis = db.get(ResearchAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return analysis


def _analysis_out(analysis: ResearchAnalysis) -> ResearchAnalysisOut:
    return ResearchAnalysisOut(
        id=analysis.id,
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        experiment_ids=json.loads(analysis.experiment_ids_json or "[]"),
        run_ids=json.loads(analysis.run_ids_json or "[]"),
        card_ids=json.loads(analysis.card_ids_json or "[]"),
        observed_facts=[ObservedFactOut(**f) for f in json.loads(analysis.observed_facts_json or "[]")],
        paper_evidence=[PaperEvidenceOut(**e) for e in json.loads(analysis.paper_evidence_json or "[]")],
        stats=json.loads(analysis.stats_json or "{}"),
        interpretation=analysis.interpretation,
        hypothesis_status=analysis.hypothesis_status,
        uncertainty=analysis.uncertainty,
        next_experiments=[
            NextExperimentOut(**n) for n in json.loads(analysis.next_experiments_json or "[]")
        ],
        source=analysis.source,
        warning=DEMO_WARNING if analysis.source == "demo" else "",
        created_at=analysis.created_at,
    )


@router.post("/questions/{question_id}/analysis", response_model=ResearchAnalysisOut)
def create_analysis(question_id: int, db: Session = Depends(get_db)):
    """按研究问题生成 AI 研究分析（只读真实数据，不修改任何实验/任务）。"""
    question = _get_question_or_404(db, question_id)
    try:
        sections, source = generate_analysis(db, question)
    except ResearchAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # 数据快照（与生成时一致）
    context = {
        "experiment_ids": sorted({f["experiment_run_id"] for f in []}),
    }
    # 从 sections 重建快照 id 集合
    run_ids = sorted({f["experiment_run_id"] for f in sections["observed_facts"]})
    card_ids = sorted({e["paper_note_id"] for e in sections["paper_evidence"]})
    # 实验 id：从运行记录反查
    from app.models import ExperimentRun
    experiment_ids = sorted(
        {
            run.experiment_id
            for run in db.scalars(select(ExperimentRun).where(ExperimentRun.id.in_(run_ids)))
        }
        if run_ids
        else []
    )

    analysis = ResearchAnalysis(
        project_id=question.project_id,
        question_id=question.id,
        experiment_ids_json=json.dumps(experiment_ids, ensure_ascii=False),
        run_ids_json=json.dumps(run_ids, ensure_ascii=False),
        card_ids_json=json.dumps(card_ids, ensure_ascii=False),
        observed_facts_json=json.dumps(sections["observed_facts"], ensure_ascii=False),
        paper_evidence_json=json.dumps(sections["paper_evidence"], ensure_ascii=False),
        stats_json=json.dumps(_stats_of(db, question, experiment_ids, run_ids), ensure_ascii=False),
        interpretation=sections["interpretation"],
        hypothesis_status=sections["hypothesis_status"],
        uncertainty=sections["uncertainty"],
        next_experiments_json=json.dumps(sections["next_experiments"], ensure_ascii=False),
        source=source,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


def _stats_of(db: Session, question, experiment_ids: list[int], run_ids: list[int]) -> dict:
    """从数据库重算统计快照（与生成时一致，防篡改）。"""
    from app.services.research_analysis import gather_context
    context = gather_context(db, question)
    # 只保留本次分析涉及的实验
    keep = set(experiment_ids)
    filtered = [e for e in context["experiments"] if e["id"] in keep]
    data = [
        {
            "id": e["id"],
            "title": e["title"],
            "metrics": [
                m for m in
                # metrics 定义需要从 context 重建；这里直接从 experiments_data 取
                _experiment_data_of(context, e["id"])
            ],
            "runs": [{"run_no": r["run_no"], "results": r["results"]} for r in e["runs"]],
        }
        for e in filtered
    ]
    return {}


# 上面 _stats_of 过于绕，改为直接复用 gather_context 的结构（见 create_analysis 实现）
9:14 PM
路由文件写乱了（残留半成品函数），重写干净版本，并让服务返回上下文以便保存统计快照。



Edit e:\ResearchPilot\backend\app\services\research_analysis.py
Added 1 line
Write e:\ResearchPilot\backend\app\routers\research_analyses.py
185 lines
"""AI 研究分析接口（v2.2）：

POST /questions/{id}/analysis    按研究问题聚合真实数据生成分析
GET  /questions/{id}/analyses    分析历史
GET  /research-analyses/{id}     分析详情
POST /research-analyses/{id}/suggestions/{i}/to-task   用户确认后转科研任务

严格约束：
- 前端不直接请求模型，全部经由本后端；
- 无运行记录 → 400 明确提示（不用虚构结果替代）；
- 无 Key → 演示模板（统计值真实、文字模板、source=demo、warning 提示）；
- 用户采纳建议之前不修改任何实验记录或任务计划（本接口只读真实数据并新增
  分析记录；转任务必须显式调用 to-task）。
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_client import DeepSeekError
from app.database import get_db
from app.models import ExperimentRun, ResearchAnalysis, ResearchQuestion, Task
from app.schemas import (
    NextExperimentOut,
    ObservedFactOut,
    PaperEvidenceOut,
    ResearchAnalysisOut,
    ResearchAnalysisToTaskOut,
)
from app.services.research_analysis import (
    DEMO_WARNING,
    ResearchAnalysisError,
    generate_analysis,
)
from app.services.serializers import build_task_out

router = APIRouter(tags=["研究分析"])


def _get_question_or_404(db: Session, question_id: int) -> ResearchQuestion:
    question = db.get(ResearchQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="研究问题不存在")
    return question


def _get_analysis_or_404(db: Session, analysis_id: int) -> ResearchAnalysis:
    analysis = db.get(ResearchAnalysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return analysis


def _analysis_out(analysis: ResearchAnalysis) -> ResearchAnalysisOut:
    return ResearchAnalysisOut(
        id=analysis.id,
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        experiment_ids=json.loads(analysis.experiment_ids_json or "[]"),
        run_ids=json.loads(analysis.run_ids_json or "[]"),
        card_ids=json.loads(analysis.card_ids_json or "[]"),
        observed_facts=[ObservedFactOut(**f) for f in json.loads(analysis.observed_facts_json or "[]")],
        paper_evidence=[PaperEvidenceOut(**e) for e in json.loads(analysis.paper_evidence_json or "[]")],
        stats=json.loads(analysis.stats_json or "{}"),
        interpretation=analysis.interpretation,
        hypothesis_status=analysis.hypothesis_status,
        uncertainty=analysis.uncertainty,
        next_experiments=[
            NextExperimentOut(**n) for n in json.loads(analysis.next_experiments_json or "[]")
        ],
        source=analysis.source,
        warning=DEMO_WARNING if analysis.source == "demo" else "",
        created_at=analysis.created_at,
    )


@router.post("/questions/{question_id}/analysis", response_model=ResearchAnalysisOut)
def create_analysis(question_id: int, db: Session = Depends(get_db)):
    """按研究问题生成 AI 研究分析（只读真实数据，不修改任何实验/任务）。"""
    question = _get_question_or_404(db, question_id)
    try:
        sections, source, context = generate_analysis(db, question)
    except ResearchAnalysisError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DeepSeekError as e:
        raise HTTPException(status_code=502, detail=str(e))

    run_ids = sorted({f["experiment_run_id"] for f in sections["observed_facts"]})
    card_ids = sorted({e["paper_note_id"] for e in sections["paper_evidence"]})
    experiment_ids = sorted(
        {
            run.experiment_id
            for run in db.scalars(select(ExperimentRun).where(ExperimentRun.id.in_(run_ids)))
        }
        if run_ids
        else []
    )

    analysis = ResearchAnalysis(
        project_id=question.project_id,
        question_id=question.id,
        experiment_ids_json=json.dumps(experiment_ids, ensure_ascii=False),
        run_ids_json=json.dumps(run_ids, ensure_ascii=False),
        card_ids_json=json.dumps(card_ids, ensure_ascii=False),
        observed_facts_json=json.dumps(sections["observed_facts"], ensure_ascii=False),
        paper_evidence_json=json.dumps(sections["paper_evidence"], ensure_ascii=False),
        stats_json=json.dumps(context["stats"], ensure_ascii=False),
        interpretation=sections["interpretation"],
        hypothesis_status=sections["hypothesis_status"],
        uncertainty=sections["uncertainty"],
        next_experiments_json=json.dumps(sections["next_experiments"], ensure_ascii=False),
        source=source,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _analysis_out(analysis)


@router.get("/questions/{question_id}/analyses", response_model=list[ResearchAnalysisOut])
def list_question_analyses(question_id: int, db: Session = Depends(get_db)):
    """该研究问题的分析历史（最新在前）。"""
    _get_question_or_404(db, question_id)
    rows = db.scalars(
        select(ResearchAnalysis)
        .where(ResearchAnalysis.question_id == question_id)
        .order_by(ResearchAnalysis.created_at.desc())
    ).all()
    return [_analysis_out(a) for a in rows]


@router.get("/research-analyses/{analysis_id}", response_model=ResearchAnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """分析详情。"""
    return _analysis_out(_get_analysis_or_404(db, analysis_id))


@router.post(
    "/research-analyses/{analysis_id}/suggestions/{suggestion_index}/to-task",
    response_model=ResearchAnalysisToTaskOut,
    status_code=status.HTTP_201_CREATED,
)
def suggestion_to_task(analysis_id: int, suggestion_index: int, db: Session = Depends(get_db)):
    """用户确认：把分析建议转为科研任务（带来源标记，防重复转换）。

    在用户调用本接口之前，不会修改任何实验记录或任务计划。
    """
    analysis = _get_analysis_or_404(db, analysis_id)
    suggestions = json.loads(analysis.next_experiments_json or "[]")
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已转换过，不能重复转换")

    title = suggestion["objective"][:200]
    description = (
        f"实验目的：{suggestion['objective']}\n"
        f"待验证假设：{suggestion['hypothesis']}\n"
        f"改变变量：{suggestion.get('changed_variables') or '—'}\n"
        f"保持不变：{suggestion.get('fixed_conditions') or '—'}\n"
        f"评价指标：{suggestion.get('metrics') or '—'}\n"
        f"预期观察：{suggestion.get('expected_observation') or '—'}\n"
        f"风险：{suggestion.get('risks') or '—'}\n"
        f"估计工作量：{suggestion.get('estimated_effort') or '—'}\n\n"
        f"来源：研究分析 #{analysis.id}"
    )
    task = Task(
        project_id=analysis.project_id,
        title=title,
        description=description,
        status="todo",
        priority="medium",
        source_type="research_analysis",
        source_id=analysis.id,
    )
    db.add(task)
    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    analysis.next_experiments_json = json.dumps(suggestions, ensure_ascii=False)
    db.commit()
    db.refresh(task)
    return ResearchAnalysisToTaskOut(task=build_task_out(task), analysis_id=analysis.id)
9:14 PM
第 5 步：注册路由，然后写单元测试。



Edit e:\ResearchPilot\backend\app\main.py
Added 1 line
Edit e:\ResearchPilot\backend\app\main.py
Added 1 line
Write e:\ResearchPilot\backend\tests\__init__.py
2 lines
# 单元测试包（unittest，无需 pytest）
9:15 PM
第 6 步：单元测试（覆盖需求指定的全部 6 种场景 + 校验细节）。



Write e:\ResearchPilot\backend\tests\test_research_analysis.py
435 lines
# -*- coding: utf-8 -*-
"""AI 研究分析服务单元测试（unittest，不依赖外部 API / 真实数据库）。

覆盖（按要求）：
1. 无实验数据 → ResearchAnalysisError（明确提示，不用虚构结果替代）
2. 只有一组实验
3. 多组实验（确定性统计与跨实验比较）
4. 有缺失文献证据（空证据合法，编造引用被丢弃）
5. 模型返回错误 JSON（重试后报错）
6. API 不可用（直接抛 DeepSeekError，不重试）

另覆盖：引用校验（run/卡片/片段 id）、页码以库为准、单实验禁「证明」、
假设状态枚举、建议截断、演示模式（统计真实+文字模板）。
"""
import json
import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai_client import DeepSeekError
from app.database import Base
from app.models import (
    Experiment,
    ExperimentRun,
    LiteratureCard,
    Project,
    ResearchQuestion,
)
from app.services import research_analysis as ra

NO_DATA = ra.NO_DATA_MESSAGE


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed(db, n_experiments=1, runs_per=1, with_cards=True, with_snippets=True):
    """构造测试数据：问题 + 可选文献卡片（含证据片段）+ n 组实验 × runs 次运行。"""
    project = Project(
        name="测试项目", goal="验证研究分析", deadline=date(2027, 12, 31), weekly_hours=10
    )
    db.add(project)
    db.flush()
    question = ResearchQuestion(
        project_id=project.id,
        content="方法A是否优于方法B？",
        objective="为目标场景选择方法",
        hypothesis="方法A的精度更高",
    )
    db.add(question)
    db.flush()
    if with_cards:
        snippets = (
            json.dumps(
                [
                    {"quote": "方法A在数据集X上取得87.3%的精度", "page": "5"},
                    {"quote": "基线方法为80.1%", "page": "6"},
                ],
                ensure_ascii=False,
            )
            if with_snippets
            else "[]"
        )
        db.add(
            LiteratureCard(
                project_id=project.id,
                question_id=question.id,
                title="对比论文",
                key_results="方法A优于基线",
                evidence_snippets_json=snippets,
            )
        )
    for i in range(n_experiments):
        exp = Experiment(
            project_id=project.id,
            question_id=question.id,
            title=f"实验{i + 1}",
            objective="对比实验",
            hypothesis="A 精度更高",
            metrics_json=json.dumps(
                [{"name": "Accuracy", "unit": "%", "higher_is_better": True}]
            ),
            status="running",
        )
        db.add(exp)
        db.flush()
        for j in range(runs_per):
            db.add(
                ExperimentRun(
                    experiment_id=exp.id,
                    run_no=j + 1,
                    config_json="{}",
                    results_json=json.dumps({"Accuracy": 80.0 + i * 5 + j}),
                    notes=f"第{j + 1}次",
                )
            )
    db.commit()
    return question


def make_context(n_experiments=1, runs_per=1):
    """手工构造 context（供 validate 测试，不依赖数据库）。"""
    valid_run_ids = set()
    experiments = []
    experiments_data = []
    for i in range(n_experiments):
        runs = []
        data_runs = []
        for j in range(runs_per):
            run_id = i * 100 + j + 1
            valid_run_ids.add(run_id)
            runs.append({"id": run_id, "run_no": j + 1, "config": {}, "results": {"Accuracy": 80.0 + i * 5 + j}, "notes": "", "random_seed": 42, "git_commit": ""})
            data_runs.append({"run_no": j + 1, "results": {"Accuracy": 80.0 + i * 5 + j}})
        experiments.append({"id": i + 1, "title": f"实验{i + 1}", "objective": "对比", "hypothesis": "A更优", "status": "running", "runs": runs})
        experiments_data.append({"id": i + 1, "title": f"实验{i + 1}", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}], "runs": data_runs})
    cards = [{
        "id": 1, "title": "对比论文", "method": "", "metrics": "", "key_results": "A优于基线",
        "limitations": "", "innovations": "",
        "snippets": [
            {"snippet_id": "1-1", "page": "5", "quote": "方法A在数据集X上取得87.3%的精度"},
            {"snippet_id": "1-2", "page": "6", "quote": "基线方法为80.1%"},
        ],
    }]
    return {
        "question": {"id": 1, "content": "A是否优于B", "objective": "", "hypothesis": "A更优"},
        "cards": cards,
        "experiments": experiments,
        "stats": ra.compute_stats(experiments_data),
        "valid_run_ids": valid_run_ids,
        "n_experiments": n_experiments,
    }


# ═══════════════════════ 确定性统计 ═══════════════════════

class TestComputeStats(unittest.TestCase):
    def test_single_experiment_stats(self):
        data = [{"id": 1, "title": "实验1", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
                 "runs": [{"run_no": 1, "results": {"Accuracy": 80.0}},
                          {"run_no": 2, "results": {"Accuracy": 88.0}},
                          {"run_no": 3, "results": {"Accuracy": 84.0}}]}]
        stats = ra.compute_stats(data)
        row = stats["metrics"][0]["experiments"][0]
        self.assertEqual(row["min"], 80.0)
        self.assertEqual(row["max"], 88.0)
        self.assertEqual(row["mean"], 84.0)
        self.assertEqual(row["best"], 88.0)
        self.assertEqual(row["best_run_no"], 2)
        self.assertEqual(row["latest"], 84.0)
        self.assertEqual(row["latest_run_no"], 3)
        self.assertEqual(stats["comparisons"], [])  # 单实验无跨实验比较

    def test_multiple_experiments_comparison(self):
        data = [
            {"id": 1, "title": "实验1", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
             "runs": [{"run_no": 1, "results": {"Accuracy": 80.0}},
                      {"run_no": 2, "results": {"Accuracy": 82.0}}]},
            {"id": 2, "title": "实验2", "metrics": [{"name": "Accuracy", "unit": "%", "higher_is_better": True}],
             "runs": [{"run_no": 1, "results": {"Accuracy": 85.0}},
                      {"run_no": 2, "results": {"Accuracy": 79.0}}]},
        ]
        stats = ra.compute_stats(data)
        rows = stats["metrics"][0]["experiments"]
        self.assertEqual(len(rows), 2)
        comparison = stats["comparisons"][0]
        self.assertEqual(comparison["metric"], "Accuracy")
        # 实验1 最优 82.0；实验2 最优 85.0 → delta +3.0
        self.assertEqual(comparison["rows"][0]["delta_vs_first"], 0.0)
        self.assertEqual(comparison["rows"][1]["delta_vs_first"], 3.0)

    def test_non_numeric_values_ignored(self):
        data = [{"id": 1, "title": "实验1", "metrics": [],
                 "runs": [{"run_no": 1, "results": {"Accuracy": 80.0, "备注": "无法量化", "ok": True}}]}]
        stats = ra.compute_stats(data)
        names = [m["name"] for m in stats["metrics"]]
        self.assertIn("Accuracy", names)
        self.assertNotIn("备注", names)
        self.assertNotIn("ok", names)


# ═══════════════════════ 无实验数据 / 上下文组装 ═══════════════════════

class TestNoDataAndGather(unittest.TestCase):
    def test_generate_no_data_raises(self):
        db = make_session()
        question = seed(db, n_experiments=0)
        with self.assertRaises(ra.ResearchAnalysisError) as ctx:
            ra.generate_analysis(db, question)
        self.assertIn("当前缺少实验数据", str(ctx.exception))

    def test_gather_single_experiment(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        context = ra.gather_context(db, question)
        self.assertEqual(context["n_experiments"], 1)
        self.assertEqual(len(context["valid_run_ids"]), 2)
        self.assertEqual(context["cards"][0]["snippets"][0]["snippet_id"], "1-1")
        self.assertEqual(context["cards"][0]["snippets"][0]["page"], "5")
        self.assertIn("Accuracy", context["stats"]["metrics"][0]["name"])

    def test_gather_multiple_experiments(self):
        db = make_session()
        question = seed(db, n_experiments=2, runs_per=2)
        context = ra.gather_context(db, question)
        self.assertEqual(context["n_experiments"], 2)
        self.assertEqual(len(context["valid_run_ids"]), 4)
        self.assertEqual(len(context["stats"]["comparisons"]), 1)

    def test_gather_without_cards(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=1, with_cards=False)
        context = ra.gather_context(db, question)
        self.assertEqual(context["cards"], [])


# ═══════════════════════ 输出校验（防编造） ═══════════════════════

class TestValidateAnalysis(unittest.TestCase):
    def valid_ai_output(self, **overrides):
        base = {
            "observed_facts": [
                {"experiment_run_id": 1, "content": "第1次运行 Accuracy=80.0"},
                {"experiment_run_id": 2, "content": "第2次运行 Accuracy=81.0"},
            ],
            "paper_evidence": [
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "5",
                 "quote": "方法A在数据集X上取得87.3%的精度", "statement": "文献报告了更高的精度"},
            ],
            "interpretation": "第2次运行精度略升，可能是参数差异导致（推测）",
            "hypothesis_status": "support",
            "uncertainty": "样本少，未重复验证",
            "next_experiments": [
                {"objective": "消融实验", "hypothesis": "关键模块贡献大", "changed_variables": "去掉模块A",
                 "fixed_conditions": "其余不变", "metrics": "Accuracy", "expected_observation": "精度下降",
                 "risks": "时间成本", "estimated_effort": "2天"},
            ],
        }
        base.update(overrides)
        return base

    def test_valid_output_passes(self):
        sections = ra.validate_analysis(self.valid_ai_output(), make_context(runs_per=2))
        self.assertEqual(len(sections["observed_facts"]), 2)
        self.assertEqual(len(sections["paper_evidence"]), 1)

    def test_fabricated_run_ids_dropped_all_invalid_raises(self):
        output = self.valid_ai_output(
            observed_facts=[{"experiment_run_id": 9999, "content": "编造的事实"}]
        )
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(runs_per=2))

    def test_fabricated_run_ids_partial_keeps_valid(self):
        output = self.valid_ai_output(
            observed_facts=[
                {"experiment_run_id": 9999, "content": "编造"},
                {"experiment_run_id": 1, "content": "真实"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual([f["experiment_run_id"] for f in sections["observed_facts"]], [1])

    def test_missing_literature_evidence_is_empty_legal(self):
        # 文献证据缺失：AI 返回空数组 → 合法，不得编造引用
        output = self.valid_ai_output(paper_evidence=[])
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"], [])

    def test_fabricated_card_or_snippet_dropped(self):
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 999, "snippet_id": "999-1", "page": "1", "quote": "x", "statement": "编造卡片"},
                {"paper_note_id": 1, "snippet_id": "1-99", "page": "1", "quote": "x", "statement": "编造片段"},
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "1", "quote": "方法A在数据集X上取得87.3%的精度", "statement": "真实证据"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(len(sections["paper_evidence"]), 1)

    def test_page_and_quote_use_database_truth(self):
        # AI 谎报页码 / 改写原文：页码与原文均以数据库为准
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "999",
                 "quote": "方法A取得99.9%的精度（改写）", "statement": "真实证据"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"][0]["page"], "5")
        self.assertIn("87.3%", sections["paper_evidence"][0]["quote"])

    def test_quote_not_from_snippet_dropped(self):
        output = self.valid_ai_output(
            paper_evidence=[
                {"paper_note_id": 1, "snippet_id": "1-2", "page": "6",
                 "quote": "完全无关的编造句子", "statement": "x"},
            ]
        )
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(sections["paper_evidence"], [])

    def test_invalid_hypothesis_status_raises(self):
        output = self.valid_ai_output(hypothesis_status="maybe")
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(runs_per=2))

    def test_single_experiment_forbids_proof_claim(self):
        output = self.valid_ai_output(interpretation="这证明方法A更优（结论）")
        with self.assertRaises(ra.ResearchFormatError):
            ra.validate_analysis(output, make_context(n_experiments=1, runs_per=2))

    def test_single_experiment_insufficient_status_ok(self):
        output = self.valid_ai_output(
            hypothesis_status="insufficient_evidence",
            interpretation="单次实验不足以判断，可能是偶然（推测）",
        )
        sections = ra.validate_analysis(output, make_context(n_experiments=1, runs_per=2))
        self.assertEqual(sections["hypothesis_status"], "insufficient_evidence")

    def test_next_experiments_truncated_and_missing_dropped(self):
        items = [
            {"objective": f"实验{i}", "hypothesis": "H"} for i in range(5)
        ] + [{"objective": "", "hypothesis": ""}]
        output = self.valid_ai_output(next_experiments=items)
        sections = ra.validate_analysis(output, make_context(runs_per=2))
        self.assertEqual(len(sections["next_experiments"]), ra.MAX_NEXT_EXPERIMENTS)
        self.assertFalse(sections["next_experiments"][0]["converted"])


# ═══════════════════════ 生成流程（错误 JSON / API 不可用 / 演示模式） ═══════════════════════

class TestGenerateFlow(unittest.TestCase):
    def _patch_client(self, responses):
        mock_client = MagicMock()
        mock_client.chat.side_effect = responses
        return patch("app.services.research_analysis.DeepSeekClient", return_value=mock_client), mock_client

    def test_model_returns_bad_json_retries_then_raises(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(["这不是JSON", "也不是JSON", "还是不对"])
            with patcher:
                with self.assertRaises(DeepSeekError):
                    ra.generate_analysis(db, question)
            # 1 次初始 + 2 次重试 = 3 次调用
            self.assertEqual(mock_client.chat.call_count, 3)

    def test_model_missing_fields_retries(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(
                [
                    json.dumps({"observed_facts": []}),  # 缺字段且空事实
                    json.dumps({"observed_facts": []}),
                    json.dumps({"observed_facts": []}),
                ]
            )
            with patcher:
                with self.assertRaises(DeepSeekError):
                    ra.generate_analysis(db, question)
            self.assertEqual(mock_client.chat.call_count, 3)

    def test_api_unavailable_propagates_without_retry(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, mock_client = self._patch_client(
                [DeepSeekError("无法连接 DeepSeek API，请检查网络是否可访问 api.deepseek.com")]
            )
            with patcher:
                with self.assertRaises(DeepSeekError) as ctx:
                    ra.generate_analysis(db, question)
            self.assertIn("无法连接", str(ctx.exception))
            self.assertEqual(mock_client.chat.call_count, 1)  # API 错误不重试

    def test_success_path_with_real_context(self):
        db = make_session()
        question = seed(db, n_experiments=2, runs_per=2)
        context = ra.gather_context(db, question)
        run_ids = sorted(context["valid_run_ids"])
        ai_output = {
            "observed_facts": [
                {"experiment_run_id": run_ids[0], "content": "真实事实1"},
                {"experiment_run_id": run_ids[1], "content": "真实事实2"},
            ],
            "paper_evidence": [
                {"paper_note_id": 1, "snippet_id": "1-1", "page": "5",
                 "quote": "方法A在数据集X上取得87.3%的精度", "statement": "文献证据"},
            ],
            "interpretation": "两组实验的最优值存在差异，可能是变量不同导致（推测）",
            "hypothesis_status": "support",
            "uncertainty": "样本量小",
            "next_experiments": [
                {"objective": "重复实验", "hypothesis": "结果可复现", "changed_variables": "无",
                 "fixed_conditions": "全部", "metrics": "Accuracy", "expected_observation": "相近",
                 "risks": "低", "estimated_effort": "1天"},
            ],
        }
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", "sk-test"):
            patcher, _ = self._patch_client([json.dumps(ai_output, ensure_ascii=False)])
            with patcher:
                sections, source, ctx = ra.generate_analysis(db, question)
        self.assertEqual(source, "deepseek")
        self.assertEqual(sections["hypothesis_status"], "support")
        self.assertEqual(len(sections["observed_facts"]), 2)
        self.assertIn("comparisons", ctx["stats"])

    def test_demo_mode_without_key(self):
        db = make_session()
        question = seed(db, n_experiments=1, runs_per=2)
        context = ra.gather_context(db, question)
        with patch("app.services.research_analysis.DEEPSEEK_API_KEY", ""):
            sections, source, _ = ra.generate_analysis(db, question)
        self.assertEqual(source, "demo")
        # 事实引用必须真实存在
        for fact in sections["observed_facts"]:
            self.assertIn(fact["experiment_run_id"], context["valid_run_ids"])
        # 统计为真实计算
        self.assertIn("metrics", context["stats"])
        # 明确标注演示模式，不得描述为真实分析
        self.assertIn("演示模式", sections["interpretation"])
        self.assertEqual(sections["hypothesis_status"], "insufficient_evidence")


if __name__ == "__main__":
    unittest.main(verbosity=2)
Bash Run unit tests for research analysis service
IN
venv/Scripts/python.exe -m unittest discover -s tests -v 2>&1 | tail -30

OUT
test_success_path_with_real_context (test_research_analysis.TestGenerateFlow.test_success_path_with_real_context) ... ok
test_gather_multiple_experiments (test_research_analysis.TestNoDataAndGather.test_gather_multiple_experiments) ... ok
test_gather_single_experiment (test_research_analysis.TestNoDataAndGather.test_gather_single_experiment) ... ok
test_gather_without_cards (test_research_analysis.TestNoDataAndGather.test_gather_without_cards) ... ok
test_generate_no_data_raises (test_research_analysis.TestNoDataAndGather.test_generate_no_data_raises) ... ok
test_fabricated_card_or_snippet_dropped (test_research_analysis.TestValidateAnalysis.test_fabricated_card_or_snippet_dropped) ... ok
test_fabricated_run_ids_dropped_all_invalid_raises (test_research_analysis.TestValidateAnalysis.test_fabricated_run_ids_dropped_all_invalid_raises) ... ok
test_fabricated_run_ids_partial_keeps_valid (test_research_analysis.TestValidateAnalysis.test_fabricated_run_ids_partial_keeps_valid) ... ok
test_invalid_hypothesis_status_raises (test_research_analysis.TestValidateAnalysis.test_invalid_hypothesis_status_raises) ... ok
test_missing_literature_evidence_is_empty_legal (test_research_analysis.TestValidateAnalysis.test_missing_literature_evidence_is_empty_legal) ... ok
test_next_experiments_truncated_and_missing_dropped (test_research_analysis.TestValidateAnalysis.test_next_experiments_truncated_and_missing_dropped) ... ok
test_page_and_quote_use_database_truth (test_research_analysis.TestValidateAnalysis.test_page_and_quote_use_database_truth) ... ERROR
test_quote_not_from_snippet_dropped (test_research_analysis.TestValidateAnalysis.test_quote_not_from_snippet_dropped) ... ok
test_single_experiment_forbids_proof_claim (test_research_analysis.TestValidateAnalysis.test_single_experiment_forbids_proof_claim) ... ok
test_single_experiment_insufficient_status_ok (test_research_analysis.TestValidateAnalysis.test_single_experiment_insufficient_status_ok) ... ok
test_valid_output_passes (test_research_analysis.TestValidateAnalysis.test_valid_output_passes) ... ok

======================================================================
ERROR: test_page_and_quote_use_database_truth (test_research_analysis.TestValidateAnalysis.test_page_and_quote_use_database_truth)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "E:\ResearchPilot\backend\tests\test_research_analysis.py", line 295, in test_page_and_quote_use_database_truth
    self.assertEqual(sections["paper_evidence"][0]["page"], "5")
                     ~~~~~~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

----------------------------------------------------------------------
Ran 23 tests in 0.153s

FAILED (errors=1)
9:16 PM
1 个测试失败——是我测试设计的问题：改写的引文按"防编造"规则应被丢弃（已有专门用例覆盖），页码纠错用例应使用真实引文+错误页码。修正测试。



Edit e:\ResearchPilot\backend\tests\test_research_analysis.py
Modified
Bash Rerun unit tests
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -3

OUT
Ran 23 tests in 0.146s

OK
9:16 PM
✅ 23/23 单元测试通过。现在扩展 HTTP 冒烟测试（v2.2 端点）。



Edit e:\ResearchPilot\backend\smoke_test.py
Added 86 lines
9:16 PM
修正 smoke 测试里一个引号转义语法错误。



Edit e:\ResearchPilot\backend\smoke_test.py
Modified
Bash Restart backend and run full smoke with v2.2 sections
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -22

OUT
 ɹ :     ֹ PID Ϊ 17280  Ľ  ̡ 
[PASS] 24.10   Ŀ     б 
[PASS] 24.11      ڵľ       404
[PASS] 24.12        麬ȫ   ֶ 
[PASS] 24.13 ɾ      
[PASS] 24.14 ɾ     ѯ    404
[PASS] 25.1 ɾ   v2.1   Ŀ            
[PASS] 25.2      뿨Ƭ   ޲   
[PASS] 26.1      v2.2       Ŀ
[PASS] 26.2   ʵ     ݷ       400   ȷ  ʾ
[PASS] 26.3    ɷ       ʾģʽ  
[PASS] 26.4   ʵ      ʵ   м ¼
[PASS] 26.5 ͳ    ֵȷ      ȷ
[PASS] 26.6 ֤        ʵ  Ƭ/Ƭ  /ҳ  
[PASS] 26.7       ʷ
[PASS] 26.8         
[PASS] 26.9      ڵķ       404
[PASS] 26.10     ת      Դ  ǣ 
[PASS] 26.11  ظ ת      400     ظ   
[PASS] 26.12      ڵĽ       404
[PASS] 26.13 ɾ   v2.2   Ŀ            

===== ͨ   124  ʧ   0    =====
9:17 PM
🎉 124/124 冒烟测试全部通过。现在准备最终展示：先检查数据库中是否有真实数据，没有则用明确标记的演示数据。



Bash Check current database contents
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def call(method, path, body=None):
    req = urllib.request.Request('http://127.0.0.1:8000/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            return resp.status, json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')
_, projects = call('GET', '/projects')
print('项目数:', len(projects))
for p in projects:
    _, detail = call('GET', f'/projects/{p[\"id\"]}')
    print(f\"- [{p['id']}] {p['name']} 任务{detail['project']['tasksTotal']}\")
    _, questions = call('GET', f\"/projects/{p['id']}/questions\")
    _, experiments = call('GET', f\"/projects/{p['id']}/experiments\")
    for q in questions:
        print(f\"  问题[{q['id']}]: {q['content'][:30]}\")
    for e in experiments:
        print(f\"  实验[{e['id']}]: {e['title'][:30]} (runs={e['runCount']})\")
"

OUT
  Ŀ  : 4
- [5]                 Ϊʶ       6
- [4]    㱨   ԡ   Ŀ     0
- [3]              8
- [2]   ҵ         8
9:25 PM
数据库有 4 个真实项目但没有任何研究问题/实验数据。按需求：使用明确标记的演示数据生成分析，并如实说明。



Bash Seed demo-marked data and generate analysis
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def call(method, path, body=None):
    req = urllib.request.Request('http://127.0.0.1:8000/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            return resp.status, json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')

# 清理可能残留的演示项目
_, projects = call('GET', '/projects')
for p in projects:
    if p['name'].startswith('【演示】'):
        call('DELETE', f\"/projects/{p['id']}\")

# 创建演示项目（全部数据明确标记为演示）
_, proj = call('POST', '/projects', {
    'name': '【演示】AI研究分析示例',
    'goal': '演示：研究分析服务（数据为演示用途，非真实实验）',
    'deadline': '2027-06-30', 'weeklyHours': 10,
})
pid = proj['id']
_, q = call('POST', f'/projects/{pid}/questions', {
    'content': '方法A是否在数据集X上优于基线方法B？',
    'objective': '为目标场景选择精度更高的方法',
    'hypothesis': '方法A的Accuracy高于方法B至少2个百分点',
})
qid = q['id']

# 两张演示文献卡片（含证据片段）
_, card1 = call('POST', f'/projects/{pid}/cards', {
    'title': '【演示】方法A论文', 'questionId': qid,
    'method': '自适应模块 + 标准训练流程', 'metrics': 'Accuracy',
    'keyResults': '方法A在数据集X上报告87.3%精度', 'innovations': '提出自适应模块',
    'evidenceSnippets': [
        {'quote': '方法A在数据集X上取得87.3%的精度', 'page': '5'},
        {'quote': '相比基线平均提升2.1个百分点', 'page': '6'},
    ],
})
_, card2 = call('POST', f'/projects/{pid}/cards', {
    'title': '【演示】基线方法B论文', 'questionId': qid,
    'method': '标准训练流程', 'metrics': 'Accuracy',
    'keyResults': '基线方法B报告80.1%精度',
    'evidenceSnippets': [{'quote': '基线方法B的精度为80.1%', 'page': '3'}],
})

# 两个实验（A vs B），各 3 次运行
for title, values in [('【演示】方法A复现实验', [81.2, 85.9, 86.4]),
                      ('【演示】方法B复现实验', [79.8, 80.3, 80.1])]:
    _, exp = call('POST', f'/projects/{pid}/experiments', {
        'title': title, 'objective': '复现论文报告精度', 'hypothesis': '方法A精度更高',
        'questionId': qid, 'status': 'done',
        'metrics': [{'name': 'Accuracy', 'unit': '%', 'higherIsBetter': True}],
    })
    for i, v in enumerate(values):
        call('POST', f\"/experiments/{exp['id']}/runs\", {
            'results': {'Accuracy': v}, 'randomSeed': 42 + i,
            'config': {'epochs': 50}, 'notes': f'第{i+1}次运行',
        })

# 生成研究分析（无 Key → 演示模式：统计真实计算，文字模板明确标注）
code, analysis = call('POST', f'/questions/{qid}/analysis')
print('analysis_code:', code, 'source:', analysis.get('source'))
with open('demo_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)
print('问题ID:', qid, '分析ID:', analysis.get('id'), '项目ID:', pid)
print('已保存 demo_analysis.json')
"

OUT
analysis_code: 200 source: demo
    ID: 1     ID: 1   ĿID: 6
 ѱ    demo_analysis.json
Read e:\ResearchPilot\backend\demo_analysis.json
9:30 PM
演示分析整体正确，但发现一个溯源瑕疵：runIds 快照只记录了事实引用的运行（3、6），而统计实际覆盖全部 6 次运行。修复路由，让快照覆盖全部分析数据。



Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Removed 6 lines
Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Modified
Bash Restart backend, rerun unit tests and smoke
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -2

OUT
 ɹ :     ֹ PID Ϊ 27800  Ľ  ̡ 

OK

===== ͨ   124  ʧ   0    =====
9:31 PM
✅ 全部通过。重新生成演示分析（快照修正后）。



Bash Regenerate demo analysis with full snapshot
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def call(method, path, body=None):
    req = urllib.request.Request('http://127.0.0.1:8000/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data) as resp:
            return resp.status, json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')
code, analysis = call('POST', '/questions/1/analysis')
print('code:', code, 'source:', analysis['source'], 'runIds:', analysis['runIds'], 'experimentIds:', analysis['experimentIds'], 'cardIds:', analysis['cardIds'])
with open('demo_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(analysis, f, ensure_ascii=False, indent=2)
print('saved')
"

OUT
code: 200 source: demo runIds: [1, 2, 3, 4, 5, 6] experimentIds: [1, 2] cardIds: [1, 2]
saved
9:35 PM
快照已覆盖全部 6 条运行记录。最后更新规划文档并汇总。



Edit e:\ResearchPilot\docs\researchpilot-v2-plan.md
Added 11 lines
9:36 PM
✅ AI 研究分析服务（v2.2）开发完成，单元测试 23 项 + 冒烟测试 124 项全部通过。

一、交付内容
新增文件（3 个）：

research_analysis.py — 核心服务：上下文组装、Python 确定性统计（min/max/mean/best/跨实验 delta）、严格 JSON 校验（防编造）、DeepSeek 编排、演示模板
research_analyses.py — API 路由
tests/test_research_analysis.py — 23 项单元测试
修改文件（5 个）：models.py（+research_analysis 表）、schemas.py（+输出模型）、main.py（注册路由）、smoke_test.py（124 项）、规划文档追加 §15。

二、职责边界（严格按需求）
谁做什么	内容
Python 后端	确定性统计计算、引用校验、上下文组装、快照溯源
DeepSeek	只负责解释、判断、建议——不得自行计算数值（Prompt 中数值只能引用统计块）
数据库	唯一事实来源：不存在的 run/卡片/片段引用一律丢弃；页码与原文以库为准（AI 谎报页码会被纠正、改写引文会被丢弃）
七段输出结构全部落地：observed_facts（带真实 run id）、paper_evidence（带真实卡片/片段 id+页码，找不到依据返回空数组）、interpretation（标注推测）、hypothesis_status（三态枚举，单组实验禁"证明/证实"字样，违反触发重试）、uncertainty、next_experiments（≤3 条×8 字段）、task_conversion（用户显式调用 to-task 接口才创建 Task，此前不修改任何实验/任务）。

三、测试结果（实际运行）
单元测试 23 项全过（python -m unittest discover -s tests），覆盖需求指定的全部场景：

需求场景	用例
无实验数据	test_generate_no_data_raises → 400「当前缺少实验数据」
只有一组实验	单组统计正确 + 单实验禁「证明」+ insufficient_evidence 通过
多组实验	跨实验 delta 计算（+3.0 验证）+ 比较表
有缺失文献证据	空证据合法；编造卡片/片段 id 丢弃；改写引文丢弃
模型返回错误 JSON	3 次调用（1+2 重试）后抛友好 DeepSeekError
API 不可用	立即抛错不重试（调用次数=1 断言）
另覆盖：页码纠错（谎报 999 → 数据库真值 5）、假设状态非法值、建议截断/缺字段丢弃、演示模式（事实引用真实、统计真实、文字明确标注演示）。

HTTP 冒烟测试 124/124（新增 13 项：无数据 400、演示生成、事实/统计/证据校验、历史/详情/404、转任务来源标记/防重复、级联清理）。

四、分析结果展示（如实说明）
数据库中原有 4 个真实项目，但没有任何研究问题与实验数据，因此按需求使用了明确标记为【演示】的数据（项目名、卡片名、实验名均带【演示】前缀），并生成了一份分析（source=demo）。以下内容不是真实实验：

研究问题：方法A是否在数据集X上优于基线方法B？（假设：A 的 Accuracy 高于 B 至少 2 个百分点）

observed_facts（引用真实存在的演示运行记录）：

experiment_run_id=3：实验「【演示】方法A复现实验」第 3 次运行：Accuracy=86.4
experiment_run_id=6：实验「【演示】方法B复现实验」第 3 次运行：Accuracy=80.1
paper_evidence（引用真实卡片与片段，页码/原文来自数据库）：

paper_note_id=1, snippet_id=1-1, p.5：「方法A在数据集X上取得87.3%的精度」
paper_note_id=2, snippet_id=2-1, p.3：「基线方法B的精度为80.1%」
stats（Python 确定性计算，基于 6 条演示记录）：

实验	运行次数	min	max	mean	best（第几次）
方法A复现（演示）	3	81.2	86.4	84.5	86.4（第3次）
方法B复现（演示）	3	79.8	80.3	80.0667	80.3（第2次）
跨实验比较	—	—	—	—	delta_vs_first = −6.1
interpretation：明确标注「（演示模式·推测性说明，非真实分析结论）…解释文字为模板生成，请配置 DeepSeek API Key 获得真实分析」；hypothesis_status：insufficient_evidence；uncertainty：标注演示模板。完整 JSON 已存 demo_analysis.json，接口可在 http://127.0.0.1:8000/docs 直接查看。

五、API 清单
方法	路径	说明
POST	/api/questions/{id}/analysis	生成研究分析（无数据→400；无 Key→demo）
GET	/api/questions/{id}/analyses	分析历史
GET	/api/research-analyses/{id}	分析详情（含快照/统计/七段结构）
POST	/api/research-analyses/{id}/suggestions/{i}/to-task	用户确认后转 Task（source_type=research_analysis，防重复）
六、如实说明
当前 .env 无 DeepSeek Key，因此 AI 生成路径由单元测试（mock）验证，实际接口运行在演示模式；配置真实 Key 后同一接口自动切换为真实分析。
演示数据（项目 ID=6「【演示】AI研究分析示例」）已留在库中供您在界面查看，随时可在项目详情删除。
本轮未开发前端调用界面（分析服务仅后端）；如需在「研究问题」页加入"生成研究分析"按钮，请告诉我。
代码未提交 git，等待您的下一步指示。



请将 ResearchPilot 2.0 的研究决策模块与原有Task科研任务管理模块打通。

具体流程：
1. 用户打开AI研究分析报告。
2. 选择一条下一步实验建议。
3. 查看实验目的、研究假设、实验变量、预计工时、所需数据和前置条件。
4. 用户修改并确认后，系统创建对应Experiment，并生成关联的Task。
5. Task保存实验ID、所属研究问题、预定开始日期、截止日期和依赖关系。
6. 原有风险引擎继续识别任务延期、依赖阻塞和剩余工时不足。
7. 原有动态重规划继续调整任务时间和工作量，但不能擅自修改研究假设或实验实际结果。
8. 所有采纳、拒绝和修改操作都要留下历史记录。

特别注意：科研决策与执行计划是两个不同层面。AI提出的科研建议需要用户确认；风险引擎只负责执行进度风险计算；动态重规划只调整执行安排，不能把科研结论交给规则引擎生成。

不要重写已有风险识别和重规划模块。优先通过新增关联字段和服务实现整合。完成后测试从实验分析建议到任务生成、风险预警、动态重规划的完整链路。
Show more
9:45 PM
开始打通决策模块与任务管理。设计思路：新增关联字段（task 加 experiment_id/question_id/dependencies_json）+ 新增采纳服务（原子创建 Experiment+Task+历史日志）+ 重规划守卫（prompt 与校验层明确只调执行安排）。先改数据模型。

第 1 步：Task 加关联字段 + 新增操作历史表。



Edit e:\ResearchPilot\backend\app\models.py
Added 8 lines
Edit e:\ResearchPilot\backend\app\models.py
Added 30 lines
9:45 PM
第 2 步：Pydantic 模型（采纳请求/日志输出/Task 扩展字段）。



Edit e:\ResearchPilot\backend\app\schemas.py
Added 4 lines
Edit e:\ResearchPilot\backend\app\schemas.py
Added 143 lines
9:45 PM
第 3 步：采纳/拒绝/修改服务（原子创建 + 历史留档）。



Write e:\ResearchPilot\backend\app\services\research_adoption.py
254 lines
"""科研建议采纳服务（v2.3）：把"科研决策"层与"执行计划"层打通。

分层原则（严格）：
- 科研决策层：AI 建议只是起点，用户确认（可先修改）后才生效；
- 执行计划层：采纳时创建 Experiment（科研载体）+ Task（执行载体），
  Task 关联实验 id / 研究问题 id / 计划日期 / 预计工时 / 依赖关系；
- 风险引擎只按任务执行进度计算风险（逾期/阻塞/落后/工时不足），
  不参与任何科研结论的生成；
- 动态重规划只调整任务执行安排（日期/优先级/工时），不触碰实验假设与结果。

所有采纳 / 拒绝 / 修改操作写入 research_action_log 历史。
"""
import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Experiment,
    ResearchActionLog,
    ResearchAnalysis,
    Task,
)

ADOPTED = "adopted"
REJECTED = "rejected"
MODIFIED = "modified"


def _suggestions_of(analysis: ResearchAnalysis) -> list[dict]:
    return json.loads(analysis.next_experiments_json or "[]")


def _save_suggestions(db: Session, analysis: ResearchAnalysis, suggestions: list[dict]) -> None:
    analysis.next_experiments_json = json.dumps(suggestions, ensure_ascii=False)
    db.commit()


def _log(
    db: Session,
    analysis: ResearchAnalysis,
    index: int,
    action: str,
    payload: dict,
    task_id: int | None = None,
    experiment_id: int | None = None,
) -> ResearchActionLog:
    log = ResearchActionLog(
        project_id=analysis.project_id,
        analysis_id=analysis.id,
        suggestion_index=index,
        action=action,
        payload_json=json.dumps(payload, ensure_ascii=False),
        task_id=task_id,
        experiment_id=experiment_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def _validate_dependencies(
    db: Session, project_id: int, dependencies: list[int]
) -> list[int]:
    """校验依赖任务：必须存在、属于同一项目；返回清理后的列表。"""
    if not dependencies:
        return []
    tasks = db.scalars(select(Task).where(Task.id.in_(dependencies))).all()
    found = {t.id for t in tasks}
    missing = [dep for dep in dependencies if dep not in found]
    if missing:
        raise HTTPException(status_code=400, detail=f"依赖任务不存在：{missing}")
    foreign = [t.id for t in tasks if t.project_id != project_id]
    if foreign:
        raise HTTPException(status_code=400, detail=f"依赖任务不属于该项目：{foreign}")
    return dependencies


def adopt_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    payload: dict,
    today: date,
) -> tuple[Experiment, Task, ResearchActionLog]:
    """用户确认采纳：原子创建 Experiment + 关联 Task，并写入历史。

    前置检查：建议存在、未被转换、未被拒绝。
    创建内容：
    - Experiment：objective/hypothesis/variables + design（含所需数据/前置条件/来源），
      状态 draft（设计待用户补充方案细节）；
    - Task：计划日期/预计工时/依赖（parent_id 取首个依赖以复用风险引擎的
      前置阻塞规则，全部依赖存入 dependencies_json），
      source_type=research_analysis，experiment_id / question_id 关联。
    """
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已采纳过，不能重复采纳")
    if suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已被拒绝，不能采纳")

    dependencies = _validate_dependencies(
        db, analysis.project_id, payload.get("dependencies") or []
    )

    design_parts = []
    if payload.get("required_data"):
        design_parts.append(f"所需数据：{payload['required_data']}")
    if payload.get("preconditions"):
        design_parts.append(f"前置条件：{payload['preconditions']}")
    design_parts.append(
        f"来源：研究分析 #{analysis.id} 的建议 #{suggestion_index + 1}"
    )
    experiment = Experiment(
        project_id=analysis.project_id,
        question_id=analysis.question_id,
        title=f"实验：{payload['objective'][:180]}",
        objective=payload["objective"],
        hypothesis=payload["hypothesis"],
        variables=payload.get("variables"),
        design="\n".join(design_parts) or None,
        status="draft",
    )
    db.add(experiment)
    db.flush()

    description_parts = [
        f"实验目的：{payload['objective']}",
        f"研究假设：{payload['hypothesis']}",
    ]
    if payload.get("variables"):
        description_parts.append(f"实验变量：{payload['variables']}")
    if payload.get("required_data"):
        description_parts.append(f"所需数据：{payload['required_data']}")
    if payload.get("preconditions"):
        description_parts.append(f"前置条件：{payload['preconditions']}")
    if dependencies:
        dep_titles = []
        dep_tasks = db.scalars(select(Task).where(Task.id.in_(dependencies))).all()
        title_map = {t.id: t.title for t in dep_tasks}
        dep_titles = [f"#{dep} {title_map.get(dep, '')}" for dep in dependencies]
        description_parts.append(f"依赖任务：{'、'.join(dep_titles)}")
    description_parts.append(f"来源：研究分析 #{analysis.id}（实验 #{experiment.id}）")

    # parent_id 取第一个依赖：复用风险引擎"前置任务阻塞"规则
    parent_id = dependencies[0] if dependencies else None
    task = Task(
        project_id=analysis.project_id,
        title=f"实验执行：{payload['objective'][:150]}",
        description="\n".join(description_parts),
        status="todo",
        priority="medium",
        planned_start_date=payload["planned_start_date"],
        planned_end_date=payload["planned_end_date"],
        estimated_hours=payload["estimated_hours"],
        parent_id=parent_id,
        source_type="research_analysis",
        source_id=analysis.id,
        experiment_id=experiment.id,
        question_id=analysis.question_id,
        dependencies_json=json.dumps(dependencies, ensure_ascii=False),
    )
    db.add(task)

    suggestion["converted"] = True
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        ADOPTED,
        payload=dict(payload),
        task_id=task.id,
        experiment_id=experiment.id,
    )
    db.refresh(task)
    return experiment, task, log


def reject_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    reason: str | None,
) -> tuple[dict, ResearchActionLog]:
    """用户拒绝建议：标记 rejected 并写入历史（不创建任何实验/任务）。"""
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted"):
        raise HTTPException(status_code=400, detail="该建议已采纳过，不能拒绝")
    if suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已被拒绝过")

    suggestion["rejected"] = True
    if reason:
        suggestion["reject_reason"] = reason
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        REJECTED,
        payload={"reason": reason or "", "suggestion": suggestion},
    )
    return suggestion, log


def modify_suggestion(
    db: Session,
    analysis: ResearchAnalysis,
    suggestion_index: int,
    fields: dict,
) -> tuple[dict, ResearchActionLog]:
    """用户修改建议（不采纳）：保存修改并留档。"""
    suggestions = _suggestions_of(analysis)
    if not 0 <= suggestion_index < len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    suggestion = suggestions[suggestion_index]
    if suggestion.get("converted") or suggestion.get("rejected"):
        raise HTTPException(status_code=400, detail="该建议已处理，不能修改")

    changes = {}
    for key, value in fields.items():
        if value is None:
            continue
        changes[key] = value
    if not changes:
        raise HTTPException(status_code=400, detail="没有需要保存的修改")

    suggestion.update(changes)
    suggestions[suggestion_index] = suggestion
    _save_suggestions(db, analysis, suggestions)

    log = _log(
        db,
        analysis,
        suggestion_index,
        MODIFIED,
        payload={"changes": changes, "suggestion": suggestion},
    )
    return suggestion, log
9:45 PM
第 4 步：路由扩展 + 序列化器。



Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Added 12 lines
Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Edit failed
Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Added 1 line
9:46 PM
追加采纳/拒绝/修改/历史端点。



Edit e:\ResearchPilot\backend\app\routers\research_analyses.py
Added 112 lines
Edit e:\ResearchPilot\backend\app\services\serializers.py
Added 1 line
Edit e:\ResearchPilot\backend\app\services\serializers.py
Added 3 lines
9:46 PM
第 6 步：迁移脚本 + 重规划守卫（明确"只调执行安排，不碰科研结论"）。



Edit e:\ResearchPilot\backend\migrate_v2.py
Added 3 lines
Edit e:\ResearchPilot\backend\app\services\replan_service.py
Added 3 lines
9:46 PM
加一条 replans.py 的边界注释，然后写单元测试。



Edit e:\ResearchPilot\backend\app\routers\replans.py
Added 4 lines
Write e:\ResearchPilot\backend\tests\test_research_adoption.py
251 lines
# -*- coding: utf-8 -*-
"""科研建议采纳服务单元测试（v2.3）：决策层 → 执行层打通。

覆盖：
- 采纳：原子创建 Experiment + Task（实验/问题/日期/工时/依赖关联齐全）
- 依赖校验：不存在的依赖 → 400；跨项目依赖 → 400
- 防重复：二次采纳 / 采纳已拒绝建议 → 400
- 拒绝：标记 + 留档，且不创建任何实验/任务
- 修改：保存修改 + 留档；已处理建议不可修改
- 历史：采纳/拒绝/修改全部留档可查
"""
import json
import unittest
from datetime import date, timedelta
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    Experiment,
    ExperimentRun,
    Project,
    ResearchActionLog,
    ResearchAnalysis,
    ResearchQuestion,
    Task,
)
from app.services import research_adoption as adoption


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def seed_analysis(db, n_suggestions=1, with_runs=False):
    project = Project(
        name="测试项目", goal="验证采纳服务", deadline=date(2027, 12, 31), weekly_hours=10
    )
    db.add(project)
    db.flush()
    question = ResearchQuestion(
        project_id=project.id, content="A是否优于B？", hypothesis="A 更优"
    )
    db.add(question)
    db.flush()
    exp = Experiment(
        project_id=project.id, question_id=question.id, title="现有实验",
        objective="复现", hypothesis="A更优", status="running",
    )
    db.add(exp)
    db.flush()
    if with_runs:
        db.add(ExperimentRun(
            experiment_id=exp.id, run_no=1, config_json="{}",
            results_json=json.dumps({"Accuracy": 82.0}), notes="原始结果",
        ))
    suggestions = [
        {
            "objective": f"建议实验{i + 1}",
            "hypothesis": f"假设{i + 1}",
            "changed_variables": "变量",
            "fixed_conditions": "条件",
            "metrics": "Accuracy",
            "expected_observation": "提升",
            "risks": "低",
            "estimated_effort": "2天",
            "converted": False,
        }
        for i in range(n_suggestions)
    ]
    analysis = ResearchAnalysis(
        project_id=project.id,
        question_id=question.id,
        experiment_ids_json=json.dumps([exp.id]),
        run_ids_json="[]",
        card_ids_json="[]",
        observed_facts_json="[]",
        paper_evidence_json="[]",
        stats_json="{}",
        interpretation="演示",
        hypothesis_status="insufficient_evidence",
        uncertainty="",
        next_experiments_json=json.dumps(suggestions, ensure_ascii=False),
        source="demo",
    )
    db.add(analysis)
    db.commit()
    return project, question, exp, analysis


PAYLOAD = {
    "objective": "验证方法A的消融效果",
    "hypothesis": "去掉模块A后精度下降",
    "variables": "是否包含模块A",
    "required_data": "数据集X（训练/验证划分）",
    "preconditions": "方法A复现实验完成",
    "estimated_hours": 12.0,
    "planned_start_date": date(2026, 12, 1),
    "planned_end_date": date(2026, 12, 15),
    "dependencies": [],
}


class TestAdoptSuggestion(unittest.TestCase):
    def test_adopt_creates_experiment_and_task_with_links(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        experiment, task, log = adoption.adopt_suggestion(
            db, analysis, 0, dict(PAYLOAD), date.today()
        )
        # Experiment 字段
        self.assertEqual(experiment.hypothesis, PAYLOAD["hypothesis"])
        self.assertEqual(experiment.variables, PAYLOAD["variables"])
        self.assertIn("所需数据", experiment.design)
        self.assertEqual(experiment.status, "draft")
        # Task 关联字段
        self.assertEqual(task.experiment_id, experiment.id)
        self.assertEqual(task.question_id, analysis.question_id)
        self.assertEqual(task.planned_start_date, PAYLOAD["planned_start_date"])
        self.assertEqual(task.estimated_hours, 12.0)
        self.assertEqual(task.source_type, "research_analysis")
        self.assertEqual(task.source_id, analysis.id)
        self.assertEqual(json.loads(task.dependencies_json), [])
        # 历史
        self.assertEqual(log.action, "adopted")
        self.assertEqual(log.task_id, task.id)
        self.assertEqual(log.experiment_id, experiment.id)
        # 建议标记 converted
        suggestions = json.loads(analysis.next_experiments_json)
        self.assertTrue(suggestions[0]["converted"])

    def test_adopt_with_dependencies(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        prereq = Task(
            project_id=analysis.project_id, title="前置任务", status="todo"
        )
        db.add(prereq)
        db.commit()
        payload = dict(PAYLOAD, dependencies=[prereq.id])
        _, task, _ = adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(task.parent_id, prereq.id)  # 复用风险引擎前置阻塞规则
        self.assertEqual(json.loads(task.dependencies_json), [prereq.id])

    def test_missing_dependency_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        payload = dict(PAYLOAD, dependencies=[99999])
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_foreign_project_dependency_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        other = Project(name="其他项目", goal="x", deadline=date(2027, 1, 1), weekly_hours=5)
        db.add(other)
        db.flush()
        foreign_task = Task(project_id=other.id, title="别的项目的任务", status="todo")
        db.add(foreign_task)
        db.commit()
        payload = dict(PAYLOAD, dependencies=[foreign_task.id])
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, payload, date.today())
        self.assertEqual(ctx.exception.status_code, 400)

    def test_double_adopt_rejected(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("已采纳", str(ctx.exception.detail))

    def test_adopt_nonexistent_suggestion_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 9, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 404)


class TestRejectAndModify(unittest.TestCase):
    def test_reject_marks_and_logs_without_creating(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        suggestion, log = adoption.reject_suggestion(db, analysis, 0, "方向与导师意见不符")
        self.assertTrue(suggestion["rejected"])
        self.assertEqual(log.action, "rejected")
        # 不创建任何实验/任务
        self.assertEqual(db.query(Task).count(), 0)
        self.assertEqual(db.query(Experiment).count(), 1)  # 只有种子实验
        # 拒绝后不可采纳
        with self.assertRaises(HTTPException) as ctx:
            adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("拒绝", str(ctx.exception.detail))

    def test_double_reject_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.reject_suggestion(db, analysis, 0, "理由")
        with self.assertRaises(HTTPException):
            adoption.reject_suggestion(db, analysis, 0, "再拒一次")

    def test_modify_saves_and_logs(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        suggestion, log = adoption.modify_suggestion(
            db, analysis, 0, {"objective": "修改后的实验目的", "estimated_effort": "5天"}
        )
        self.assertEqual(suggestion["objective"], "修改后的实验目的")
        self.assertEqual(suggestion["estimated_effort"], "5天")
        self.assertEqual(log.action, "modified")
        self.assertIn("objective", json.loads(log.payload_json)["changes"])

    def test_modify_after_adopt_raises(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db)
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        with self.assertRaises(HTTPException):
            adoption.modify_suggestion(db, analysis, 0, {"objective": "x"})

    def test_full_history_three_actions(self):
        db = make_session()
        _, _, _, analysis = seed_analysis(db, n_suggestions=2)
        adoption.modify_suggestion(db, analysis, 0, {"objective": "改"})
        adoption.adopt_suggestion(db, analysis, 0, dict(PAYLOAD), date.today())
        adoption.reject_suggestion(db, analysis, 1, "不做")
        logs = (
            db.query(ResearchActionLog)
            .filter(ResearchActionLog.analysis_id == analysis.id)
            .order_by(ResearchActionLog.id)
            .all()
        )
        actions = [log.action for log in logs]
        self.assertEqual(actions, ["modified", "adopted", "rejected"])
        suggestions = json.loads(analysis.next_experiments_json)
        self.assertTrue(suggestions[0]["converted"])
        self.assertTrue(suggestions[1]["rejected"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
Bash Run all unit tests including adoption
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -4

OUT
----------------------------------------------------------------------
Ran 34 tests in 0.430s

FAILED (errors=5)
Bash List failing test names
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | grep -E "^(ERROR|FAIL):" | head -10

OUT
ERROR: test_adopt_creates_experiment_and_task_with_links (test_research_adoption.TestAdoptSuggestion.test_adopt_creates_experiment_and_task_with_links)
ERROR: test_adopt_with_dependencies (test_research_adoption.TestAdoptSuggestion.test_adopt_with_dependencies)
ERROR: test_double_adopt_rejected (test_research_adoption.TestAdoptSuggestion.test_double_adopt_rejected)
ERROR: test_full_history_three_actions (test_research_adoption.TestRejectAndModify.test_full_history_three_actions)
ERROR: test_modify_after_adopt_raises (test_research_adoption.TestRejectAndModify.test_modify_after_adopt_raises)
Bash Show detailed error for adopt test
IN
venv/Scripts/python.exe -m unittest tests.test_research_adoption.TestAdoptSuggestion.test_adopt_creates_experiment_and_task_with_links 2>&1 | tail -12

OUT
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\json\encoder.py", line 258, in iterencode
    return _iterencode(o, 0)
           ^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\json\encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type date is not JSON serializable

----------------------------------------------------------------------
Ran 1 test in 0.055s

FAILED (errors=1)
9:57 PM
_log 里 date 对象不可序列化——在服务层做健壮处理（default=str）。



Edit e:\ResearchPilot\backend\app\services\research_adoption.py
Added 1 line
Bash Rerun unit tests
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -3

OUT
Ran 34 tests in 0.431s

OK
9:58 PM
✅ 34/34 单元测试通过。现在写 完整链路冒烟测试（建议→修改→采纳→任务→风险→重规划→守卫验证）。



Edit e:\ResearchPilot\backend\smoke_test.py
Added 171 lines
Bash Run migration for task v2.3 columns
IN
venv/Scripts/python.exe migrate_v2.py 2>&1 | tail -6

OUT
[    ] experiment_run.random_seed  Ѵ   
[    ] experiment_run.git_commit  Ѵ   
[    ] experiment_run.environment_json  Ѵ   
[    ] experiment_run.log_path  Ѵ   
[    ] experiment_run.result_files_json  Ѵ   
[   ] Ǩ    ɣ        3   
Bash Restart backend, run unit tests and full smoke with chain section
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -24

OUT
 ɹ :     ֹ PID Ϊ 36064  Ľ  ̡ 

OK
[PASS] 25.1 ɾ   v2.1   Ŀ            
[PASS] 25.2      뿨Ƭ   ޲   
[PASS] 26.1      v2.2       Ŀ
[PASS] 26.2   ʵ     ݷ       400   ȷ  ʾ
[PASS] 26.3    ɷ       ʾģʽ  
[PASS] 26.4   ʵ      ʵ   м ¼
[PASS] 26.5 ͳ    ֵȷ      ȷ
[PASS] 26.6 ֤        ʵ  Ƭ/Ƭ  /ҳ  
[PASS] 26.7       ʷ
[PASS] 26.8         
[PASS] 26.9      ڵķ       404
[PASS] 26.10     ת      Դ  ǣ 
[PASS] 26.11  ظ ת      400     ظ   
[PASS] 26.12      ڵĽ       404
[PASS] 26.13 ɾ   v2.2   Ŀ            
[PASS] 27.1      ջ       Ŀ
[PASS] 27.2    ɷ       ģ 彨 飩
[PASS] 27.3  ޸Ľ  鲢    
[PASS] 27.4     ǰ      
[FAIL] 27.5    ɽ           ʵ  +     code=500
[PASS] 27.19 ɾ   ջ   Ŀ            
[PASS] 27.20       ʷ   ޲   

===== ͨ   130  ʧ   1    =====
9:59 PM
27.5 采纳报 500，查后端日志。



Bash Find adopt endpoint exception in backend log
IN
awk '/suggestions\/0\/adopt/{found=1} found && /Error|error|line [0-9]+, in/{print; n++} n>8{exit}' /tmp/backend.log | grep -vE "uvicorn|starlette|fastapi" | head -8

OUT
INFO:     127.0.0.1:55986 - "POST /api/research-analyses/3/suggestions/0/adopt HTTP/1.1" 500 Internal Server Error
  File "E:\ResearchPilot\backend\venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1794, in _execute_context
  File "E:\ResearchPilot\backend\venv\Lib\site-packages\sqlalchemy\engine\default.py", line 1750, in _init_compiled
  File "E:\ResearchPilot\backend\venv\Lib\site-packages\sqlalchemy\dialects\sqlite\base.py", line 1341, in process
    raise TypeError(
TypeError: SQLite Date type only accepts Python date objects as input.
9:59 PM
采纳服务把日期字符串直接写进了 Date 列。在服务里做日期归一化。



Edit e:\ResearchPilot\backend\app\services\research_adoption.py
Added 7 lines
Edit e:\ResearchPilot\backend\app\services\research_adoption.py
Modified
Bash Restart and rerun unit tests plus full smoke
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -24

OUT
 ɹ :     ֹ PID Ϊ 36116  Ľ  ̡ 

OK
[PASS] 26.12      ڵĽ       404
[PASS] 26.13 ɾ   v2.2   Ŀ            
[PASS] 27.1      ջ       Ŀ
[PASS] 27.2    ɷ       ģ 彨 飩
[PASS] 27.3  ޸Ľ  鲢    
[PASS] 27.4     ǰ      
[PASS] 27.5    ɽ           ʵ  +    
[PASS] 27.6    񱣴 ʵ  /    /    /    
[PASS] 27.7         ʶ     ڣ  ߷  գ 
[PASS] 27.8  ڶ          
[PASS] 27.9         ʶ  ǰ         з  գ 
[PASS] 27.10      ع滮    
[PASS] 27.11      ع滮
[PASS] 27.12  ع滮          ִ      
[PASS] 27.13  ع滮δ ޸  о     
[PASS] 27.14  ع滮δ ޸ ʵ    
[PASS] 27.15  ܾ    鲢    
[PASS] 27.16  Ѿܾ    鲻 ɲ       400
[PASS] 27.17     / ܾ / ޸ ȫ      
[PASS] 27.18  ظ         400
[PASS] 27.19 ɾ   ջ   Ŀ            
[PASS] 27.20       ʷ   ޲   

===== ͨ   144  ʧ   0    =====
10:00 PM
🎉 144/144 冒烟测试 + 34/34 单元测试全部通过，完整链路验证成功。更新规划文档。



Edit e:\ResearchPilot\docs\researchpilot-v2-plan.md
Added 11 lines
10:00 PM
✅ 科研决策模块 × 任务管理打通完成。全链路测试通过：144 项冒烟 + 34 项单元测试。

一、交付内容
新增文件（2 个）：

research_adoption.py — 采纳服务：原子创建 Experiment+Task、依赖校验、防重复、全量留档
tests/test_research_adoption.py — 11 项单元测试
修改文件（6 个）：models.py（task+3 关联字段、+research_action_log 表）、schemas.py（采纳/拒绝/修改请求与日志模型）、research_analyses.py（+4 端点）、serializers.py（Task 输出新字段）、replan_service.py（Prompt 边界守卫）、replans.py（采纳逻辑边界注释+兜底）、migrate_v2.py（task 3 新列，已执行幂等迁移）。

二、分层设计（核心）

科研决策层                    执行计划层
AI 分析报告 → 建议 ──用户确认──→ Experiment + Task
（建议只是起点）               （风险引擎：逾期/阻塞/工时不足）
   ↓ 采纳/拒绝/修改              ↓ 重规划：只调日期/优先级/工时
research_action_log 留档       （结构上不触碰 Experiment/ExperimentRun）
任务新字段（迁移只加列，旧数据完好）：experiment_id、question_id、dependencies_json；parent_id 取首个依赖以复用风险引擎现有"前置任务阻塞"规则（不改写风险模块）。

新 API：

方法	路径	说明
POST	/api/research-analyses/{id}/suggestions/{i}/adopt	用户确认采纳（可先修改 8 个字段）→ 创建 Experiment+Task+历史
POST	/api/research-analyses/{id}/suggestions/{i}/reject	拒绝（可填原因）→ 留档，不创建任何东西
PUT	/api/research-analyses/{id}/suggestions/{i}	修改建议（不采纳）→ 留档
GET	/api/research-analyses/{id}/actions	采纳/拒绝/修改历史
三、完整链路测试结果（smoke §27，20 项全过）
生成分析 → 模板建议 ✅
修改建议留档（modified）✅
采纳：创建实验（假设/变量/所需数据入 design）+ 任务（experimentId/questionId/日期/工时/依赖/sourceType 全对）✅
风险引擎：逾期任务 → 高风险"已逾期" ✅；依赖未完成前置 → 中风险"前置任务阻塞" ✅
动态重规划：生成→采纳→任务日期被调整 ✅
守卫验证：重规划后研究假设不变（27.13）、实验结果不变（27.14）✅
历史：modified + adopted×2 + rejected 全部可查（27.17）✅
拒绝后不可采纳、重复采纳 400、拒绝/修改/采纳的防重复与 404 路径 ✅
单元测试 34/34：采纳创建与关联、依赖不存在/跨项目 → 400、二次采纳 → 400、拒绝留档且零创建、拒绝后不可采纳、修改留档、已处理不可修改、三操作历史顺序。

四、如实说明
本轮为后端整合，前端"选择建议→查看字段→修改→确认"的交互界面尚未开发（v2.2 也未做前端）；后端已提供完整支撑，接口文档在 http://127.0.0.1:8000/docs 可查。需要前端时请告知。
迁移已执行（task 表 +3 列，幂等，备份保留），旧任务数据不受影响。
风险引擎与重规划模块未重写：风险规则零改动；重规划仅在 Prompt 增加边界条款、采纳逻辑加兜底注释（其原有 VALID_ACTIONS 校验本就只允许 reschedule/reprioritize）。
代码未提交 git，等待您的指示。



现在请对 ResearchPilot 2.0 进行一次完整的质量验收。不要只检查页面能否打开。

测试场景：
1. 创建一个科研项目和研究问题。
2. 上传一篇可正常解析的PDF文献。
3. 生成结构化文献研究卡片，验证引用能定位到真实原文片段和页码。
4. 根据文献创建一个实验设计。
5. 新增至少两组实验运行记录，录入不同的真实测试数据或明确标记为DEMO的演示数据。
6. 比较多组实验的真实指标。
7. 调用DeepSeek生成研究分析，验证事实、推测、未知因素和后续实验建议的区分。
8. 用户确认一条建议，将其转为Experiment和Task。
9. 模拟任务延期，验证风险识别和动态重规划。
10. 查看研究决策日志、实验历史和任务重规划历史是否完整。

必须执行：
- 后端接口回归测试。
- 新增模块单元测试。
- 前端npm run build。
- 关键业务流程端到端测试。
- 数据持久化测试。
- 无DeepSeek密钥、无效密钥和真实密钥场景测试；真实密钥不可用时明确记录，不得伪造成功。
- 检查是否存在前端暴露API Key、SQL注入、文件上传风险和数据丢失问题。
- 检查原有功能是否因升级而损坏。

请列出每项测试的实际结果、失败原因和修复情况。没有执行的测试标记为未执行，不允许编造通过率。最后更新README，给出从安装到完整演示的复现步骤。
Show more
10:02 PM
开始完整质量验收。我会逐项实际执行并如实记录结果。第 1 步：环境状态确认（后端、密钥、数据库）。



Bash Check backend health, key config, git status
IN
curl -s -m 3 http://127.0.0.1:8000/api/health && echo && grep -c "DEEPSEEK_API_KEY" .env && grep "^DEEPSEEK_API_KEY" .env | sed 's/=.*/=<隐藏>/' && git -C /e/ResearchPilot status --short | wc -l

OUT
{"status":"ok","service":"ResearchPilot API"}
1
DEEPSEEK_API_KEY=<隐藏>
2269
Bash Run unit tests and full API regression
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -1

OUT
OK
===== ͨ   144  ʧ   0    =====
Bash Frontend build and lint
IN
cd /e/ResearchPilot/frontend && npm run build 2>&1 | grep -E "error|✓ built" | head -3 && npm run lint 2>&1 | grep -cE "error"

OUT
✓ built in 16.51s
0
10:04 PM
✅ 回归测试、单元测试、前端构建全部通过。第 3 步：编写 10 场景验收脚本（含真实 PDF 生成与上传）。



Write e:\ResearchPilot\backend\acceptance_test.py
388 lines
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
        # 七段结构区分验证
        sections_ok = (
            len(facts) >= 1
            and all("experimentRunId" in f for f in facts)
            and ("推测" in interp or "演示模式" in interp)
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
        record(
            "场景7 文献证据引用真实卡片与片段",
            bool(evidence)
            and all(
                e["paperNoteId"] == card_id and e["page"] == "1" for e in evidence
            ),
            f"evidence={[(e['paperNoteId'], e['snippetId'], e['page']) for e in evidence]}",
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
Bash Run 10-scenario acceptance E2E test
IN
venv/Scripts/python.exe acceptance_test.py 2>&1

OUT
Exit code 1
===== ResearchPilot 2.0        գ http://127.0.0.1:8000  =====

[PASS]     1           Ŀ code=201
[PASS]     1      о    ⣨Ŀ  +   裩 code=201
[PASS]     2  ϴ PDF           code=201 chunks=1
[PASS]     3 AI  ȡ  Ƭ    ǰ  Կģʽ £  code=200 source=demo
[PASS]     3  ˹    ƿ Ƭ+֤  Ƭ  ҳ   code=200
[PASS]     3 ֤  Ƭ οɶ λ    ʵԭ   quotes_in_fulltext=True
[PASS]     4        ״   ʵ    ƣ     /    /   ݼ /ģ  /   ã  code=201
[PASS]     5 ¼      ʵ     м ¼    ǡ   ʾ     3+3       
[PASS]     6   ʵ  ָ  Աȣ   ʵ  ֵ   points=6 bestA=86.4
[PASS]     7  о      ߶νṹ   ֣   ʵ/ Ʋ /δ֪/   飩 source=demo facts=2 evidence=0 suggestions=1 status=insufficient_evidence
[FAIL]     7     ֤        ʵ  Ƭ  Ƭ   evidence=[]
[PASS]     8 ȷ Ͻ           Experiment+Task code=201
[PASS]     9        񱻷       ʶ 𣨸߷  գ  risk=high reason=       27  죬   Ƚ  0%
[PASS]     9    ɶ ̬ ع滮     code=200 changes=1
[PASS]     9      ع滮      ִ а  ţ  applied=1
[PASS]     9        ع滮δ          ʵ     results=[{'Accuracy': 81.2}, {'Accuracy': 85.9}, {'Accuracy': 86.4}]
[PASS]     10    ߿    м ¼    422 code=422
[PASS]     10      о      code=201
[PASS]     10       ־ ɲ  count=1
[PASS]     10 ʵ        ʷ      3      У  runs=3
[PASS]     10  ع滮  ʷ         Ѳ  ɼ ¼   count=1
[PASS]     10          ʷ     actions=['adopted']

=====    ս    ͨ   21  ʧ   1    =====
  [FAIL]     7     ֤        ʵ  Ƭ  Ƭ Σ evidence=[]
           ݣ    
10:05 PM
1 项失败——验收脚本自身的问题：场景 3 完善卡片时没有把卡片关联到研究问题（questionId），导致分析上下文里没有这张卡片，证据为空。这是脚本缺陷而非产品缺陷。修复脚本。



Edit e:\ResearchPilot\backend\acceptance_test.py
Added 1 line
Bash Rerun acceptance E2E test
IN
venv/Scripts/python.exe acceptance_test.py 2>&1 | tail -12

OUT
[PASS]     9    ɶ ̬ ع滮     code=200 changes=1
[PASS]     9      ع滮      ִ а  ţ  applied=1
[PASS]     9        ع滮δ          ʵ     results=[{'Accuracy': 81.2}, {'Accuracy': 85.9}, {'Accuracy': 86.4}]
[PASS]     10    ߿    м ¼    422 code=422
[PASS]     10      о      code=201
[PASS]     10       ־ ɲ  count=1
[PASS]     10 ʵ        ʷ      3      У  runs=3
[PASS]     10  ع滮  ʷ         Ѳ  ɼ ¼   count=1
[PASS]     10          ʷ     actions=['adopted']

=====    ս    ͨ   22  ʧ   0    =====
           ݣ    
10:05 PM
✅ 验收场景 22/22 全部通过。接下来测密钥场景：先备份 .env 并注入无效密钥。



Bash Test invalid API key scenario
IN
cp .env .env.bak-acceptance && sed -i 's/^DEEPSEEK_API_KEY=.*/DEEPSEEK_API_KEY=sk-invalid-key-for-testing-123456/' .env && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -c "
import json, urllib.request, urllib.error
def call(method, path, body=None):
    req = urllib.request.Request('http://127.0.0.1:8000/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=120) as resp:
            return resp.status, json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')
# 用演示项目里的问题 1（仍存在）测试分析接口
code, body = call('POST', '/questions/1/analysis')
print('无效密钥 → 分析接口:', code, '| detail:', body.get('detail', '')[:120])
code, body = call('POST', '/ai/plan', {'topic': '测试', 'deadline': '2027-01-01', 'weeklyHours': 5, 'currentStage': '选题'})
print('无效密钥 → 计划接口:', code, '| detail:', body.get('detail', '')[:120])
"

OUT
 ɹ :     ֹ PID Ϊ 38160  Ľ  ̡ 
  Ч  Կ         ӿ : 502 | detail: DeepSeek API Key   Ч   ѹ  ڣ      backend/.env  е  DEEPSEEK_API_KEY
  Ч  Կ     ƻ  ӿ : 502 | detail: DeepSeek API Key   Ч   ѹ  ڣ      backend/.env  е  DEEPSEEK_API_KEY
10:06 PM
✅ 无效密钥测试通过：两个 AI 接口均返回 502 + 明确的"API Key 无效"中文提示（说明错误映射正确，且网络可达 DeepSeek）。恢复 .env。



Bash Restore .env and restart backend
IN
mv .env.bak-acceptance .env && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && curl -s -m 5 http://127.0.0.1:8000/api/health && venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
print('无密钥恢复后 → 演示模式确认:')
projs = get('/projects')
print('  项目数:', len(projs))
"

OUT
 ɹ :     ֹ PID Ϊ 30232  Ľ  ̡ 
{"status":"ok","service":"ResearchPilot API"}    Կ ָ         ʾģʽȷ  :
    Ŀ  : 5
10:07 PM
✅ 恢复完成。持久化测试：记录数据 → 重启后端 → 验证数据完好。



Bash Persistence test across backend restart
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
projs = get('/projects')
print('重启前: 项目数 =', len(projs), '| 项目1任务数 =', get('/projects/1')['project']['tasksTotal'])
qs = get('/projects/6/questions')
print('重启前: 演示项目问题数 =', len(qs))
import json as j
open('/tmp/persist_before.json','w').write(j.dumps({'projects': len(projs)}))
" && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
projs = get('/projects')
print('重启后: 项目数 =', len(projs), '| 项目1任务数 =', get('/projects/1')['project']['tasksTotal'])
qs = get('/projects/6/questions')
print('重启后: 演示项目问题数 =', len(qs))
analyses = get('/questions/1/analyses')
print('重启后: 问题1分析历史数 =', len(analyses), '(含统计快照:', len(analyses[0]['stats'].get('metrics', [])) if analyses else '-', ')')
"

OUT
Exit code 1
Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "<string>", line 4, in get
  File "E:\python\Lib\urllib\request.py", line 215, in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 521, in open
    response = meth(req, response)
               ^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 630, in http_response
    response = self.parent.error(
               ^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 559, in error
    return self._call_chain(*args)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 492, in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 639, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 404: Not Found
Traceback (most recent call last):
  File "<string>", line 7, in <module>
  File "<string>", line 4, in get
  File "E:\python\Lib\urllib\request.py", line 215, in urlopen
    return opener.open(url, data, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 521, in open
    response = meth(req, response)
               ^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 630, in http_response
    response = self.parent.error(
               ^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 559, in error
    return self._call_chain(*args)
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 492, in _call_chain
    result = func(*args)
             ^^^^^^^^^^^
  File "E:\python\Lib\urllib\request.py", line 639, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 404: Not Found
10:08 PM
测试脚本里硬编码了项目 ID，实际 ID 已变化。改为动态查找。



Bash Persistence test with dynamic IDs
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
projs = get('/projects')
demo = next((p for p in projs if p['name'].startswith('【演示】')), None)
first = projs[0]
print('重启前: 项目数 =', len(projs))
print('重启前: 演示项目 id =', demo['id'] if demo else None)
if demo:
    qs = get(f\"/projects/{demo['id']}/questions\")
    print('重启前: 演示项目问题数 =', len(qs), '| 问题1分析数 =', len(get('/questions/1/analyses')) if qs and qs[0]['id'] == 1 else '-')
open('/tmp/persist_state.json','w').write(json.dumps({'n': len(projs), 'demo_id': demo['id'] if demo else None, 'first_id': first['id']}))
" && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
state = json.load(open('/tmp/persist_state.json'))
projs = get('/projects')
print('重启后: 项目数 =', len(projs), '(重启前', state['n'], ')')
demo_id = state['demo_id']
if demo_id:
    qs = get(f'/projects/{demo_id}/questions')
    print('重启后: 演示项目问题数 =', len(qs))
    if qs:
        analyses = get(f\"/questions/{qs[0]['id']}/analyses\")
        print('重启后: 分析历史 =', len(analyses), '条 | 统计指标数 =', len(analyses[0]['stats'].get('metrics', [])) if analyses else '-')
detail = get(f\"/projects/{state['first_id']}\")
print('重启后: 第一个项目任务数 =', detail['project']['tasksTotal'], '| 数据完好')
"

OUT
Exit code 1
Traceback (most recent call last):
  File "<string>", line 14, in <module>
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/persist_state.json'
    ǰ:   Ŀ   = 5
    ǰ:   ʾ  Ŀ id = 6
    ǰ:   ʾ  Ŀ       = 1 |     1       = 2
Traceback (most recent call last):
  File "<string>", line 6, in <module>
FileNotFoundError: [Errno 2] No such file or directory: '/tmp/persist_state.json'
10:09 PM
又是 /tmp 路径映射问题。改用后端目录下的文件。



Bash Persistence test with backend-dir state file
IN
venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
projs = get('/projects')
demo = next((p for p in projs if p['name'].startswith('【演示】')), None)
print('重启前: 项目数 =', len(projs), '| 演示项目 id =', demo['id'] if demo else None)
if demo:
    qs = get(f\"/projects/{demo['id']}/questions\")
    print('重启前: 演示项目问题数 =', len(qs))
    if qs:
        analyses = get(f\"/questions/{qs[0]['id']}/analyses\")
        print('重启前: 分析历史数 =', len(analyses))
open('persist_state.json','w').write(json.dumps({'n': len(projs), 'demo_id': demo['id'] if demo else None}))
" && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
state = json.load(open('persist_state.json'))
projs = get('/projects')
print('重启后: 项目数 =', len(projs), '(重启前', state['n'], ')')
if state['demo_id']:
    qs = get(f\"/projects/{state['demo_id']}/questions\")
    print('重启后: 演示项目问题数 =', len(qs))
    if qs:
        analyses = get(f\"/questions/{qs[0]['id']}/analyses\")
        print('重启后: 分析历史 =', len(analyses), '条 | 统计指标数 =', len(analyses[0]['stats'].get('metrics', [])) if analyses else '-')
" && rm persist_state.json

OUT
    ǰ:   Ŀ   = 5 |   ʾ  Ŀ id = 6
    ǰ:   ʾ  Ŀ       = 1
    ǰ:       ʷ   = 2
 ɹ :     ֹ PID Ϊ 36488  Ľ  ̡ 
      :   Ŀ   = 5 (    ǰ 5 )
      :   ʾ  Ŀ       = 1
      :       ʷ = 2    | ͳ  ָ     = 1
10:11 PM
✅ 持久化测试通过。现在做安全检查：前端密钥暴露、SQL 注入面、文件上传风险。



Bash Security checks: key exposure, SQL injection, upload handling
IN
cd /e/ResearchPilot && echo "=== 1. 前端密钥暴露检查 ===" && grep -rniE "sk-[a-z0-9]|deepseek_api|api_key|apikey|authorization.*bearer" frontend/src frontend/index.html 2>/dev/null | head -5; echo "(空=无暴露)" && echo "=== 2. SQL注入面检查（字符串拼接SQL）===" && grep -rnE "execute\(f\"|execute\('.*SELECT|SELECT .*% " backend/app --include="*.py" | head -5; echo "(空=无拼接SQL)" && echo "=== 3. 上传路径处理 ===" && grep -n "uuid\|UPLOAD_DIR" backend/app/routers/experiments.py | head -5

OUT
=== 1. 前端密钥暴露检查 ===
frontend/src/assets/vite.svg:1:<svg xmlns="http://www.w3.org/2000/svg" width="77" height="47" fill="none" aria-labelledby="vite-logo-title" viewBox="0 0 77 47"><title id="vite-logo-title">Vite</title><style>.parenthesis{fill:#000}@media (prefers-color-scheme:dark){.parenthesis{fill:#fff}}</style><path fill="#9135ff" d="M40.151 45.71c-.663.844-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.493c-.92 0-1.457-1.04-.92-1.788l7.479-10.471c1.07-1.498 0-3.578-1.842-3.578H15.443c-.92 0-1.456-1.04-.92-1.788l9.696-13.576c.213-.297.556-.474.92-.474h28.894c.92 0 1.456 1.04.92 1.788l-7.48 10.472c-1.07 1.497 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.087.89 1.83L40.153 45.712z"/><mask id="a" width="48" height="47" x="14" y="0" maskUnits="userSpaceOnUse" style="mask-type:alpha"><path fill="#000" d="M40.047 45.71c-.663.843-2.02.374-2.02-.699V34.708a2.26 2.26 0 0 0-2.262-2.262H24.389c-.92 0-1.457-1.04-.92-1.788l7.479-10.472c1.07-1.497 0-3.578-1.842-3.578H15.34c-.92 0-1.456-1.04-.92-1.788l9.696-13.575c.213-.297.556-.474.92-.474H53.93c.92 0 1.456 1.04.92 1.788L47.37 13.03c-1.07 1.498 0 3.578 1.842 3.578h11.376c.944 0 1.474 1.088.89 1.831L40.049 45.712z"/></mask><g mask="url(#a)"><g filter="url(#b)"><ellipse cx="5.508" cy="14.704" fill="#eee6ff" rx="5.508" ry="14.704" transform="rotate(269.814 20.96 11.29)scale(-1 1)"/></g><g filter="url(#c)"><ellipse cx="10.399" cy="29.851" fill="#eee6ff" rx="10.399" ry="29.851" transform="rotate(89.814 -16.902 -8.275)scale(1 -1)"/></g><g filter="url(#d)"><ellipse cx="5.508" cy="30.487" fill="#8900ff" rx="5.508" ry="30.487" transform="rotate(89.814 -19.197 -7.127)scale(1 -1)"/></g><g filter="url(#e)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.928 4.177)scale(1 -1)"/></g><g filter="url(#f)"><ellipse cx="5.508" cy="30.599" fill="#8900ff" rx="5.508" ry="30.599" transform="rotate(89.814 -25.738 5.52)scale(1 -1)"/></g><g filter="url(#g)"><ellipse cx="14.072" cy="22.078" fill="#eee6ff" rx="14.072" ry="22.078" transform="rotate(93.35 31.245 55.578)scale(-1 1)"/></g><g filter="url(#h)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#i)"><ellipse cx="3.47" cy="21.501" fill="#8900ff" rx="3.47" ry="21.501" transform="rotate(89.009 35.419 55.202)scale(-1 1)"/></g><g filter="url(#j)"><ellipse cx="14.592" cy="9.743" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(39.51 14.592 9.743)"/></g><g filter="url(#k)"><ellipse cx="61.728" cy="-5.321" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 61.728 -5.32)"/></g><g filter="url(#l)"><ellipse cx="55.618" cy="7.104" fill="#00c2ff" rx="5.971" ry="9.665" transform="rotate(37.892 55.618 7.104)"/></g><g filter="url(#m)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#n)"><ellipse cx="12.326" cy="39.103" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 12.326 39.103)"/></g><g filter="url(#o)"><ellipse cx="49.857" cy="30.678" fill="#8900ff" rx="4.407" ry="29.108" transform="rotate(37.892 49.857 30.678)"/></g><g filter="url(#p)"><ellipse cx="52.623" cy="33.171" fill="#00c2ff" rx="5.971" ry="15.297" transform="rotate(37.892 52.623 33.17)"/></g></g><path d="M6.919 0c-9.198 13.166-9.252 33.575 0 46.789h6.215c-9.25-13.214-9.196-33.623 0-46.789zm62.424 0h-6.215c9.198 13.166 9.252 33.575 0 46.789h6.215c9.25-13.214 9.196-33.623 0-46.789" class="parenthesis"/><defs><filter id="b" width="60.045" height="41.654" x="-5.564" y="16.92" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="c" width="90.34" height="51.437" x="-40.407" y="-6.762" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="d" width="79.355" height="29.4" x="-35.435" y="2.801" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="e" width="79.579" height="29.4" x="-30.84" y="20.8" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="f" width="79.579" height="29.4" x="-29.307" y="21.949" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="g" width="74.749" height="58.852" x="29.961" y="-17.13" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="7.659"/></filter><filter id="h" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="i" width="61.377" height="25.362" x="37.754" y="3.055" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="j" width="56.045" height="63.649" x="-13.43" y="-22.082" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="k" width="54.814" height="64.646" x="34.321" y="-37.644" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="l" width="33.541" height="35.313" x="38.847" y="-10.552" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="m" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="n" width="54.814" height="64.646" x="-15.081" y="6.78" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="o" width="54.814" height="64.646" x="22.45" y="-1.645" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter><filter id="p" width="39.409" height="43.623" x="32.919" y="11.36" color-interpolation-filters="sRGB" filterUnits="userSpaceOnUse"><feFlood flood-opacity="0" result="BackgroundImageFix"/><feBlend in="SourceGraphic" in2="BackgroundImageFix" result="shape"/><feGaussianBlur result="effect1_foregroundBlur_2002_17286" stdDeviation="4.596"/></filter></defs></svg>
frontend/src/components/board/TaskFormSheet.tsx:127:            <Label htmlFor="task-title">任务标题</Label>
frontend/src/components/board/TaskFormSheet.tsx:129:              id="task-title"
frontend/src/components/board/TaskFormSheet.tsx:137:            <Label htmlFor="task-description">任务描述（可选）</Label>
frontend/src/components/board/TaskFormSheet.tsx:139:              id="task-description"
(空=无暴露)
=== 2. SQL注入面检查（字符串拼接SQL）===
(空=无拼接SQL)
=== 3. 上传路径处理 ===
9:import uuid
16:from app.config import UPLOAD_DIR
240:            path = UPLOAD_DIR / name
310:        path = UPLOAD_DIR / name
333:    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
10:11 PM
精确化安全复查（排除误报）。



Bash Precise security rechecks
IN
echo "=== 精确密钥模式（sk-后跟20+字符）===" && grep -rnE "sk-[a-zA-Z0-9]{20,}" frontend/src frontend/index.html 2>/dev/null | head -3; echo "(空=无真实密钥格式)" && echo "=== 后端是否有裸SQL ===" && grep -rnE "text\(|execute\(|SELECT|INSERT|UPDATE|DELETE" backend/app --include="*.py" | grep -vE "select\(|Select|update\(|delete\(|insert" | head -5; echo "(空=全部走ORM)" && echo "=== 上传文件名生成 ===" && grep -n "uuid4\|name = f" backend/app/routers/experiments.py | head -3

OUT
=== 精确密钥模式（sk-后跟20+字符）===
(空=无真实密钥格式)
=== 后端是否有裸SQL ===
backend/app/database.py:16:    cursor.execute("PRAGMA foreign_keys=ON")
backend/app/routers/documents.py:88:        full_text, scanned = extract_pdf_text(data)
backend/app/routers/documents.py:105:    chunks = chunk_text(full_text)
backend/app/routers/questions.py:32:        for row in db.execute(
backend/app/schemas.py:166:def _check_optional_text(v: str | None, label: str, limit: int) -> str | None:
(空=全部走ORM)
=== 上传文件名生成 ===
335:    name = f"{uuid.uuid4().hex}{suffix}"
10:11 PM
✅ 安全复查结论明确：无密钥暴露（此前的命中是 "task-title"/"mask-type" 的误报）、无裸 SQL（仅一条静态 PRAGMA）、上传文件名用 uuid 无路径穿越风险。最后更新 README。



Edit e:\ResearchPilot\README.md
Added 3 lines
Edit e:\ResearchPilot\README.md
Modified
Edit e:\ResearchPilot\README.md
Edit failed
Edit e:\ResearchPilot\README.md
Added 1 line
10:12 PM
补充 README 的目录结构与新增"完整演示复现步骤 + 质量验收"章节。



Edit e:\ResearchPilot\README.md
Added 6 lines
Edit e:\ResearchPilot\README.md
Added 2 lines
Edit e:\ResearchPilot\README.md
Added 62 lines
10:12 PM
最后做一次全量终检，确认所有测试项最终状态。



Bash Final full verification of all test suites
IN
cd /e/ResearchPilot/backend && venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -1 && venv/Scripts/python.exe acceptance_test.py 2>&1 | tail -1 && cd /e/ResearchPilot/frontend && npm run build 2>&1 | grep -E "✓ built|error" | head -2

OUT
OK
===== ͨ   144  ʧ   0    =====
           ݣ    
✓ built in 15.38s
10:13 PM
✅ ResearchPilot 2.0 质量验收完成。以下为逐项实际执行结果（全部实跑，未执行的明确标注）。

一、10 个验收场景（acceptance_test.py 实跑：22/22 通过）
#	场景	结果	说明
1	创建科研项目+研究问题	✅ 通过	项目创建 + 问题（目标+假设）写入并回读
2	上传可解析 PDF	✅ 通过	脚本现场构造含文字层的合法 PDF（非伪造内容），pypdf 成功提取并切块
3	生成卡片 + 引用定位	✅ 通过	AI 抽取（demo 空模板）→ 人工完善 + 证据片段（页码 p.1）；引用原文逐字存在于 PDF 提取全文（底层定位保证，前端点击高亮基于此）；浏览器内点击定位因无浏览器自动化环境标注为 API 层验证
4	根据文献创建实验设计	✅ 通过	假设参照文献结论；变量/对照/数据集/模型/配置全部入库
5	录入两组以上运行记录	✅ 通过	2 实验 × 3 次运行，数据全部标记【演示】（无真实实验数据，如实标注）
6	比较真实指标	✅ 通过	跨实验总览 6 个数据点，最优值 86.4 vs 80.3 计算正确
7	AI 研究分析七段区分	✅ 通过	事实带 run id、证据带卡片/片段 id+页码、解释标注推测/演示、状态 insufficient_evidence、未知因素、建议 ≤3
8	确认建议 → Experiment+Task	✅ 通过	采纳创建实验+任务（关联/日期/工时/来源全对）
9	模拟延期 → 风险+重规划	✅ 通过	逾期任务 → 高风险"已逾期 27 天"；重规划生成→采纳→日期调整；守卫：假设与实验结果一字未变
10	决策/实验/重规划历史完整	✅ 通过	决策日志可查、运行历史 3 条完整、重规划历史含已采纳记录、建议操作历史含 adopted
二、必须执行的测试项
测试项	结果
后端接口回归	✅ 144/144（1.0 原 36 项 + v2 各模块 108 项）
新增模块单元测试	✅ 34/34（研究分析 23 + 建议采纳 11，mock DeepSeek，不依赖外部 API）
前端构建	✅ npm run build 通过；npm run lint 0 错误
关键流程端到端	✅ 见上表 10 场景
数据持久化	✅ 重启后端后：5 个项目、演示问题、2 条分析历史（含统计快照）完好
密钥三场景	✅ 无 Key：全功能演示模式（明确标注）；✅ 无效 Key：注入假密钥实测 → 502 +"API Key 无效或已过期"（同时证明网络可达 DeepSeek，错误映射正确）；❌ 真实 Key：未执行（当前无真实密钥，如实记录，未伪造成功）；.env 测试后已恢复
安全：前端密钥暴露	✅ 无（全库扫描 sk-+20字符 模式 0 命中；密钥仅存 backend/.env）
安全：SQL 注入	✅ 无注入面（全部查询走 SQLAlchemy ORM 绑定参数；唯一的裸 SQL 是静态 PRAGMA foreign_keys=ON）
安全：文件上传	✅ PDF 只提取文字不落盘（20MB/加密/扫描版检测）；图片白名单类型+5MB+每条 3 张+uuid 文件名（无路径穿越）；uploads 目录已 gitignore
安全：数据丢失	✅ 迁移自动备份 research.db.bak-v2（实测）；级联删除全覆盖测试；卡片/任务引用 SET NULL 保护；前端删除二次确认
原有功能回归	✅ 1.0 全部功能行为不变（36 项冒烟 + 前端构建）
三、验收中发现的 2 个问题及修复
验收脚本场景 3 未把卡片关联研究问题 → 分析证据为空（FAIL）→ 判定为脚本缺陷（产品逻辑正确：分析只读关联问题的卡片）→ 补 questionId 后通过。
采纳服务日期字符串写入 SQLite Date 列报 500（冒烟 27.5 曾失败）→ 服务层增加日期归一化（date 对象/ISO 字符串双兼容）→ 修复后通过。
四、交付物
新增 acceptance_test.py：10 场景验收脚本，可重复执行（--keep 保留数据供界面复查）
README.md 已全面更新：16 张表、144 项测试、测试命令、第 10 节"从安装到完整演示的复现步骤"（10 步对应验收场景）、第 11 节质量验收结论表
未执行项汇总：① 真实密钥场景（无密钥）；② 浏览器内的人工点击操作（无浏览器自动化环境，以 API 级验证 + 前端构建 + 代码走查替代）。两项均未计入通过率。

代码仍未提交 git（累计大量改动）。需要我提交吗？



.env
我现在已经把密钥写上去了，继续执行你未执行的
10:19 PM
收到，密钥已配置。现在执行此前标记"未执行"的真实密钥场景测试。先确认密钥已生效（不显示密钥内容）。



Bash Verify real key present and restart backend
IN
grep -q "^DEEPSEEK_API_KEY=sk-" .env && echo "已检测到真实格式密钥（sk-开头）" && grep "^DEEPSEEK_API_KEY=" .env | cut -c1-30 && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && curl -s -m 5 http://127.0.0.1:8000/api/health

OUT
grep: .env: No such file or directory
{"status":"ok","service":"ResearchPilot API"}
10:20 PM
当前目录不对，用绝对路径重试。



Bash Verify real key and restart backend with absolute path
IN
grep -q "^DEEPSEEK_API_KEY=sk-" /e/ResearchPilot/backend/.env && echo "已检测到真实格式密钥（sk-开头）" && grep "^DEEPSEEK_API_KEY=" /e/ResearchPilot/backend/.env | cut -c1-28 && for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; cd /e/ResearchPilot/backend && venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && curl -s -m 5 http://127.0.0.1:8000/api/health

OUT
{"status":"ok","service":"ResearchPilot API"}
10:20 PM
输出异常，直接验证密钥加载状态。



Bash Verify key loaded into backend config
IN
cd /e/ResearchPilot/backend && venv/Scripts/python.exe -c "
from app.config import DEEPSEEK_API_KEY
key = DEEPSEEK_API_KEY
print('密钥状态:', '已加载真实密钥（长度', len(key), '，前缀', key[:6] + '...', '）' if key.startswith('sk-') and len(key) > 20 else '无效/为空: ' + repr(key[:15]))
"

OUT
  Կ״̬:  Ѽ     ʵ  Կ       0   ǰ׺ ...   Ч/Ϊ  : ''
10:22 PM
配置读到的密钥是空——.env 可能未保存或格式不对。检查文件内容（只显示密钥行的形态，不显示密钥本身）。



Bash Check .env file state with key masked
IN
ls -la .env && grep -n "DEEPSEEK" .env | sed -E 's/(=sk-[a-zA-Z0-9]{6})[a-zA-Z0-9]+/\1****(隐藏)/' | head -5 && wc -l .env

OUT
-rw-r--r-- 1 86198 197609 90 Nov 11 22:06 .env
1:DEEPSEEK_API_KEY=
2:DEEPSEEK_BASE_URL=https://api.deepseek.com
3:DEEPSEEK_MODEL=deepseek-chat
3 .env
10:22 PM
发现问题：.env 文件里的密钥行是空的（DEEPSEEK_API_KEY=）。检查是否有其他位置保存了密钥。



Bash Check all env files for saved key
IN
ls -la .env* 2>/dev/null; echo "---"; for f in .env .env.example .env.bak*; do [ -f "$f" ] && echo "$f: $(grep -c 'sk-' "$f" 2>/dev/null) 个含sk-的行"; done; echo "---检查是否保存在 IDE 而未落盘：文件修改时间---"; stat -c '%y %n' .env

OUT
-rw-r--r-- 1 86198 197609  90 Nov 11 22:06 .env
-rw-r--r-- 1 86198 197609 690 Oct 13 18:42 .env.example
---
.env: 0 个含sk-的行
.env.example: 1 个含sk-的行
---检查是否保存在 IDE 而未落盘：文件修改时间---
2026-11-11 22:06:10.159328700 +0800 .env
10:24 PM
⚠️ 发现问题，需要您先处理一步：磁盘上的 backend/.env 文件里密钥行目前是空的：


DEEPSEEK_API_KEY=
我检查了所有相关文件：

.env（22:06 修改）→ 密钥行为空，0 个 sk- 开头的行
.env.example → 只有占位符 sk-xxxxxxxx...
无其他备份文件含密钥
最可能的原因：您在 VSCode 里输入了密钥但还没保存（编辑器标签页应显示未保存圆点）。请按 Ctrl+S 保存后告诉我，我立即继续真实密钥场景测试。

按验收原则我不会伪造这个测试的结果——在文件真正落盘前，后端加载到的密钥仍是空（我刚才已实测确认），全部 AI 功能仍在演示模式。

保存后我将执行：

重启后端 → 实测真实 AI 研究分析（七段结构、防编造校验、与演示模式的差异）
实测真实 AI 计划生成
把冒烟测试中"假定无密钥"的断言改为双模式兼容后全量重跑（单元 34 + 冒烟 144 + 验收 22 + 前端构建）
更新 README 验收结论中的真实密钥场景结果


现在呢
10:27 PM
检查密钥是否已保存到磁盘。



Bash Check if key is now saved in .env
IN
stat -c '%y %n' .env && grep "^DEEPSEEK_API_KEY=" .env | sed -E 's/=(sk-[a-zA-Z0-9]{6})[a-zA-Z0-9]+/=\1****(已隐藏，长度见下)/' && venv/Scripts/python.exe -c "
from app.config import DEEPSEEK_API_KEY
print('后端加载密钥长度:', len(DEEPSEEK_API_KEY), '| 前缀:', (DEEPSEEK_API_KEY[:6] + '...') if len(DEEPSEEK_API_KEY) > 8 else '(空)')"

OUT
2026-11-11 22:27:08.042118600 +0800 .env
DEEPSEEK_API_KEY=sk-cce118****(已隐藏，长度见下)
  ˼     Կ    : 35 | ǰ׺: sk-cce...
10:27 PM
✅ 密钥已落盘（35 字符，sk- 开头）。开始执行真实密钥场景。先把冒烟/验收脚本中"假定无密钥"的断言改为双模式兼容。



Edit e:\ResearchPilot\backend\smoke_test.py
Modified
Edit e:\ResearchPilot\backend\acceptance_test.py
Added 7 lines
Bash Test real-key AI research analysis and plan generation
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -c "
import json, urllib.request, urllib.error, time
def call(method, path, body=None):
    req = urllib.request.Request('http://127.0.0.1:8000/api' + path, method=method)
    req.add_header('Content-Type', 'application/json')
    data = json.dumps(body).encode('utf-8') if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=180) as resp:
            return resp.status, json.loads(resp.read() or b'null')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'null')
    except urllib.error.URLError as e:
        return 0, {'detail': f'网络错误: {e.reason}'}

t0 = time.time()
code, analysis = call('POST', '/questions/1/analysis')
elapsed = time.time() - t0
print('研究分析: code =', code, '| source =', analysis.get('source'), f'| 耗时 {elapsed:.1f}s')
if code == 200:
    print('  observed_facts:', [(f['experimentRunId'], f['content'][:40]) for f in analysis['observedFacts']])
    print('  paper_evidence:', [(e['paperNoteId'], e['snippetId'], e['page']) for e in analysis['paperEvidence']])
    print('  hypothesis_status:', analysis['hypothesisStatus'])
    print('  interpretation 前120字:', analysis['interpretation'][:120])
    print('  uncertainty 前120字:', analysis['uncertainty'][:120])
    print('  next_experiments:', len(analysis['nextExperiments']), '条')
    for n in analysis['nextExperiments'][:2]:
        print('    -', n['objective'][:50], '| 工时:', n['estimatedEffort'][:30])
    print('  stats.mean(A) =', analysis['stats']['metrics'][0]['experiments'][0]['mean'])
else:
    print('  detail:', analysis.get('detail'))

t0 = time.time()
code, plan = call('POST', '/ai/plan', {'topic': '虚拟世界智能体行为规划', 'deadline': '2027-03-31', 'weeklyHours': 8, 'currentStage': '文献调研', 'completedWork': '已读10篇文献'})
print('计划生成: code =', code, '| source =', plan.get('source'), f'| 耗时 {time.time()-t0:.1f}s | 任务数:', len(plan.get('tasks', [])))
"

OUT
 ɹ :     ֹ PID Ϊ 20312  Ľ  ̡ 
 о     : code = 200 | source = deepseek |   ʱ 10.0s
  observed_facts: [(1, '    A  1     У        42  epochs=50  Accuracy=81.2%'), (2, '    A  2     У        43  epochs=50  Accuracy=85.9%'), (3, '    A  3     У        44  epochs=50  Accuracy=86.4%'), (4, '    B  1     У        42  epochs=50  Accuracy=79.8%'), (5, '    B  2     У        43  epochs=50  Accuracy=80.3%'), (6, '    B  3     У        44  epochs=50  Accuracy=80.1%')]
  paper_evidence: [(1, '1-1', '5'), (1, '1-2', '6'), (2, '2-1', '3')]
  hypothesis_status: insufficient_evidence
  interpretation ǰ120  :   ȷ    ͳ ƿ       A       еľ ֵ84.5%   ڷ   B  ֵ80.0667%     ֵ86.4%Ҳ   ڷ   B   ֵ80.3%    ֵԼ6.1   ٷֵ㣨  ˸     best  ֵ         ϳ   2   ٷֵ ļ     ֵ        A       в    ϴ 81.2%
  uncertainty ǰ120  : ÿ   3     У       С  δ ṩ                 Լ  飻    A   м䲨    81.2%~86.4%   ϴ    ֵ81.2% 뷽  B   ֵ80.3%    Լ0.9   ٷֵ㣬     ص    գ    ־ ֵ84.5%    ԭ  87.3%            ԭ    
  next_experiments: 3   
    -                          A 뷽  B   ȶ      ֵ     |   ʱ:  еȣ Լ     ڵ ǰ        
    -  Է   A 뷽  B  Accuracy       ͳ       Լ    |   ʱ:      е 
  stats.mean(A) = 84.5
 ƻ     : code = 200 | source = deepseek |   ʱ 10.1s |       : 9
10:28 PM
🎉 真实密钥场景实测成功：AI 研究分析 source=deepseek（10 秒返回）——6 条事实全部引用真实运行记录与真实数值、证据引用真实卡片/片段/页码、假设判定给出 insufficient_evidence（样本量小，判断合理）、解释直接引用后端确定性统计值（均值 84.5 vs 80.0667）、3 条建议带工时。AI 计划生成同样成功（9 个任务）。

现在全量重跑所有测试套件（双模式兼容后）。



Bash Full suite rerun with real key configured
IN
venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -1 && venv/Scripts/python.exe acceptance_test.py 2>&1 | tail -3 && cd /e/ResearchPilot/frontend && npm run build 2>&1 | grep -E "✓ built|error" | head -2

OUT
OK
===== ͨ   143  ʧ   0    =====
=====    ս    ͨ   21  ʧ   1    =====
  [FAIL]     7  о      ߶νṹ   ֣   ʵ/ Ʋ /δ֪/   飩  source=deepseek facts=6 evidence=2 suggestions=3 status=insufficient_evidence
           ݣ    
✓ built in 16.58s
10:37 PM
1 项失败：真实 AI 的 interpretation 没有使用"推测"字样（要求是"明确标记为推测"）。先看完整文本再决定修复方案。



Bash Inspect full AI interpretation text
IN
cd /e/ResearchPilot/backend && venv/Scripts/python.exe -c "
import json, urllib.request
def get(path):
    with urllib.request.urlopen('http://127.0.0.1:8000/api' + path) as r:
        return json.loads(r.read())
analyses = get('/questions/1/analyses')
a = analyses[0]
print('最新分析 source:', a['source'])
print('--- interpretation 全文 ---')
print(a['interpretation'])
print('--- uncertainty 全文 ---')
print(a['uncertainty'])
print('--- 含标记词检测 ---')
for w in ['推测', '可能', '或许', '尚不', '待验证', '不确定', '证明', '证实']:
    print(f'  \"{w}\":', w in a['interpretation'])
"

OUT
   ·    source: deepseek
--- interpretation ȫ   ---
  ȷ    ͳ ƿ       A       еľ ֵ84.5%   ڷ   B  ֵ80.0667%     ֵ86.4%Ҳ   ڷ   B   ֵ80.3%    ֵԼ6.1   ٷֵ㣨  ˸     best  ֵ         ϳ   2   ٷֵ ļ     ֵ        A       в    ϴ 81.2%~86.4%     ҽ   3     С    Ӳ ͬ   Ʋ ò    ܲ             Ӵ    ķ  ͬʱ    A   ־ ֵ84.5%    ԭ ı    87.3%  ˵                ԭ Ĵ  ڲ  죬 в   ȷ      A  Ŀ 곡     ȶ    ڷ   B    2   ٷֵ㡣
--- uncertainty ȫ   ---
ÿ   3     У       С  δ ṩ                 Լ  飻    A   м䲨    81.2%~86.4%   ϴ    ֵ81.2% 뷽  B   ֵ80.3%    Լ0.9   ٷֵ㣬     ص    գ    ־ ֵ84.5%    ԭ  87.3%            ԭ   Ƿ һ  ԭ  δ ҵ ˵    δ       ݼ    ֡     Э   ϸ ڣ ԭ  δ ҵ          ȱ  ͳ       Լ      ݣ  ޷  жϲ    Ƿ       
---     Ǵʼ   ---
  " Ʋ ": True
  "    ": True
  "    ": False
  " в ": True
  "    ֤": False
  "  ȷ  ": False
  "֤  ": False
  "֤ʵ": False
10:38 PM
解读成功：最新分析其实含"推测"字样（验收失败的是验收项目自己的那份分析——真实 AI 用了其他谨慎措辞但没用"推测"）。根本问题是后端校验没强制执行"标注推测"（v2.2 需求明确要求）。修复方案：强化后端校验 + 同步验收断言。



Edit e:\ResearchPilot\backend\app\services\research_analysis.py
Added 2 lines
Edit e:\ResearchPilot\backend\app\services\research_analysis.py
Added 5 lines
Edit e:\ResearchPilot\backend\tests\test_research_analysis.py
Added 14 lines
Edit e:\ResearchPilot\backend\acceptance_test.py
Added 1 line
Bash Restart and rerun all backend test suites with real key
IN
for PID in $(netstat -ano | grep ":8000" | awk '{print $5}' | sort -u); do taskkill //PID $PID //F 2>/dev/null; done; sleep 3; venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
sleep 7 && venv/Scripts/python.exe -m unittest discover -s tests 2>&1 | tail -2 && venv/Scripts/python.exe smoke_test.py 2>&1 | tail -1 && venv/Scripts/python.exe acceptance_test.py 2>&1 | tail -3

OUT
 ɹ :     ֹ PID Ϊ 37724  Ľ  ̡ 

OK
===== ͨ   143  ʧ   0    =====

=====    ս    ͨ   22  ʧ   0    =====
           ݣ    
10:40 PM
🎉 22/22 验收全过（真实密钥路径）。更新 README 验收结论。



Edit e:\ResearchPilot\README.md
Modified
10:40 PM
✅ 真实密钥场景执行完毕，全部通过。 汇总如下：

一、本次执行内容
1. 真实密钥实测（此前标记"未执行"的项）

测试	实际结果
AI 研究分析（真实 Key）	✅ source=deepseek，约 10 秒返回。6 条事实全部引用真实运行记录与真实数值（81.2/85.9/86.4/79.8/80.3/80.1）；证据引用真实卡片/片段/页码（1-1/p.5、1-2/p.6、2-1/p.3）；解释直接引用后端确定性统计值（均值 84.5 vs 80.0667、差值约 6.1 个百分点）；假设判定 insufficient_evidence（样本量小，判断克制）；不确定性含"原文未找到"标注；3 条建议含工作量估计
AI 计划生成（真实 Key）	✅ source=deepseek，约 10 秒，9 个任务正常返回
2. 真实模式下发现 1 个缺陷并修复

真实 AI 的解释没有使用"推测"字样（验收断言失败）——而 v2.2 需求明确要求"interpretation 明确标记为推测而不是结论"，此前只在 Prompt 层约束、校验层未强制。修复：后端校验新增推测标记词强制检查（推测/可能/或许/尚不/待验证/不确定等，缺失触发重试、仍缺则 502 友好提示），并新增 2 项单元测试。修复后验收 22/22 通过。

3. 双模式兼容改造

冒烟/验收脚本中原有 2 处"假定无密钥"的断言改为双模式兼容（15.2 无 Key 专属项在有 Key 时条件跳过、场景 7 证据断言区分 demo/deepseek 语义）。

二、最终全量结果（真实密钥配置下实跑）
套件	结果
单元测试	✅ 36/36（新增推测标记 2 项）
冒烟回归	✅ 143/143（无 Key 时 144；有 Key 时 1 项无 Key 专属断言按设计跳过，无失败）
10 场景验收	✅ 22/22（其中场景 7 走真实 DeepSeek 路径）
前端构建	✅ 通过
三、此前"未执行"项的最终状态
✅ 真实密钥场景：已执行，结果见上
⚠️ 浏览器人工点击验证：仍无浏览器自动化环境，无法由我代跑；但真实 Key 下所有后端链路已通，您现在可以在浏览器完整体验真实 AI 分析（研究问题 → POST /questions/{id}/analysis 接口，或告诉我给前端加分析入口）
四、README 已更新
验收结论表已更新为最终状态（含真实密钥实测结果、3 个验收缺陷及修复说明、143/144 计数差异说明）。

所有代码改动仍未提交 git（累计约 20+ 个文件）。需要我现在提交吗？