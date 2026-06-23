# 暮橙体育记账本

给姐姐开发的电商记账本桌面应用，用于管理销售记录、采购单和开单打印。

## 功能

- **仪表盘**：本月/本年经营概览、近 6 个月趋势、客户/产品/厂家排行、收款和任务行动项
- **销售记录**：记录每笔交易的金额、成本、交易方式，自动计算毛利润和利润率
- **采购单**：记录从各工厂拿货的数量和金额
- **开单**：向客户开具销售单并打印
- **数据总览**：按日/周/月查看销售、毛利、采购和分布图表

## 技术栈

- 后端：FastAPI + SQLModel + SQLite + loguru，通过 uv 管理环境
- 前端：React + TypeScript + Ant Design
- 桌面壳：PyWebView
- 打包：Windows 使用 Nuitka + Inno Setup，macOS 暂保留 PyInstaller + dmg
- CI：GitHub Actions 自动构建 Windows 和 Mac 安装包

## 本地开发

```bash
# 启动后端（终端 1）
cd backend
uv run python main.py --dev

# 启动前端（终端 2）
cd frontend
pnpm dev
```

浏览器访问 `http://localhost:5173`
网页打开，支持热重载

后端会把结构化日志写入系统数据目录下的 `logs/sis-book.log`。开发时可以用 `SIS_BOOK_DATA=/path/to/data` 指定数据目录，用 `SIS_BOOK_LOG_LEVEL=DEBUG` 调整日志级别。

## 验证

```bash
cd backend
uv run pytest -q

cd ../frontend
pnpm lint
pnpm build
```

## 正式版（桌面应用）

```bash
# 编译前端（终端1）
cd frontend
pnpm build

# 使用 pywebview 启动后端（终端2）
cd backend
uv run python main.py
```

启动桌面应用。桌面端和后端服务日志会写入数据目录，便于排查打包后的问题。

## 发版

Windows 本地打包需要先构建前端，然后在 Windows 上执行：

```powershell
cd frontend
pnpm build
cd ..
pwsh ./build/windows-package.ps1 -Version dev
```

macOS 打包链路暂时仍使用 `build/sis-book.spec`。

在开发完成已经提交并push后执行
```bash
git tag v1.0.0  # 替换为实际标签
git push --tags
```

GitHub Actions 自动构建，在 Releases 页面下载 `mucheng_setup.exe`。
