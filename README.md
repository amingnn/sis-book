# 暮橙体育记账本

给姐姐开发的电商记账本桌面应用，用于管理销售记录、采购单和开单打印。

## 功能

- **仪表盘**：本月/本年销售概览、未结清订单提醒
- **销售记录**：记录每笔交易的金额、成本、交易方式，自动计算毛利润和利润率
- **采购单**：记录从各工厂拿货的数量和金额
- **开单**：向客户开具销售单并打印

## 技术栈

- 后端：Python + FastAPI + SQLModel + SQLite
- 前端：React + TypeScript + Ant Design
- 桌面壳：PyWebView
- 打包：PyInstaller + Inno Setup
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

## 正式版（桌面应用）

```bash
# 编译前端（终端1）
cd frontend
pnpm build

# 使用 pywebview 启动后端（终端2）
cd backend
uv run python main.py
```

启动桌面应用，无日志不建议开发使用

## 发版

在开发完成已经提交并push后执行
```bash
git tag v1.0.0  # 替换为实际标签
git push --tags
```

GitHub Actions 自动构建，在 Releases 页面下载 `mucheng_setup.exe`。
