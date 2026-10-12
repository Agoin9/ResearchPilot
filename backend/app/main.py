"""FastAPI 应用入口：CORS、路由注册、启动建表、全局异常处理。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.database import init_db
from app.routers import ai, documents, home, projects, replans, report, reports, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时建表（表已存在则跳过，数据保留）
    init_db()
    yield


app = FastAPI(
    title="ResearchPilot API",
    description="研途智控后端服务：项目 / 任务 / 进度记录 / 重规划历史（基础数据管理）",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS 跨域配置 ────────────────────────────────────────────────────
# 开发期放开本地跨域；正式部署再收紧。
#
# 1) allow_origins：显式列出前端本地开发服务器的来源（localhost:5174 是当前
#    实际端口；5173 是默认端口，两者都放行以兼容端口漂移）。
# 2) allow_origin_regex：兜底放行任意本地端口的 localhost / 127.0.0.1 来源
#    （例如 Vite 因端口被占用自动 +1 到 5175 的情况）。
# 3) allow_credentials=True：支持带凭据（Cookie/Authorization）的跨域请求。
#    注意：开了 credentials 就不能再返回 Access-Control-Allow-Origin: *，
#    Starlette 会自动回显请求的精确来源，两者均已满足。
# 4) allow_private_network=True：放行 Chrome 的 Private Network Access（PNA）
#    预检。浏览器从 http://localhost:5174 这类本地页面直连
#    http://127.0.0.1:8000 时，Chrome 130+（尤其系统开着代理时）会把请求视为
#    跨地址空间访问，先发带 Access-Control-Request-Private-Network: true 的
#    OPTIONS 预检；不开启此开关，Starlette 会返回 400 拒绝预检，请求被浏览器
#    静默拦截，前端表现为「无法连接后端服务」。
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_private_network=True,
)

app.include_router(projects.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(home.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(report.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(replans.router, prefix="/api")


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """参数校验错误统一返回 422 + 中文提示。

    注意：当请求体包含非 UTF-8 字节（如 Windows 终端 curl 发中文时的 GBK 编码）时，
    exc.errors() 的 input 字段可能是 bytes。FastAPI 默认处理器会把它交给
    jsonable_encoder 做 o.decode()（UTF-8），触发 UnicodeDecodeError 导致 500。
    这里先做安全转换，再走 jsonable_encoder（它能处理 ctx 里挂着的异常对象），
    保证永远返回明确的 422 错误而不是 Internal Server Error。
    """
    errors = []
    for err in exc.errors():
        item = dict(err)
        if isinstance(item.get("input"), (bytes, bytearray)):
            item["input"] = "<非 UTF-8 编码的请求数据>"
            if tuple(item.get("loc", ())) == ("body",):
                # 请求体整个无法解析：给出可操作的提示
                item["msg"] = (
                    "请求体无法解析：请使用 UTF-8 编码的 JSON 提交"
                    "（Windows 终端 curl 发中文时的 GBK 编码会导致此问题）"
                )
        # pydantic 会把 ValueError 包装成 "Value error, xxx"，去掉前缀让提示更直接
        msg = item.get("msg")
        if isinstance(msg, str) and msg.startswith("Value error, "):
            item["msg"] = msg[len("Value error, "):]
        errors.append(item)
    return JSONResponse(
        status_code=422, content={"detail": jsonable_encoder(errors)}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """HTTP 错误统一返回 {"detail": ...}，并把请求体解析错误换成中文提示。"""
    detail = exc.detail
    if detail == "There was an error parsing the body":
        detail = (
            "请求体不是合法的 JSON（或包含非 UTF-8 编码的中文），"
            "请使用 UTF-8 编码提交"
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：任何未处理异常都返回 JSON（详细堆栈仍会打印到后端日志）。"""
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请查看后端启动窗口的日志"},
    )


@app.get("/api/health", tags=["系统"])
def health():
    """健康检查：确认后端服务已启动。"""
    return {"status": "ok", "service": "ResearchPilot API"}
