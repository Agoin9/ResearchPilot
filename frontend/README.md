# ResearchPilot 前端

React + TypeScript + Vite + Tailwind CSS + shadcn/ui + Recharts。

## 启动说明

前端通过 axios 请求 `/api` 接口，Vite 开发服务器会把 `/api` 代理到后端 `http://127.0.0.1:8000`，
因此需要**先启动后端**（见 [../backend/README.md](../backend/README.md)），再启动前端：

```bash
cd frontend
npm install        # 首次使用
npm run dev        # 启动后访问 http://localhost:5173
```

常用命令：`npm run build`（类型检查 + 构建）、`npm run lint`（代码检查）。

---

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.
