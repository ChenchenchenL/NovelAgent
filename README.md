# NovelAgent

个人小说创作 Agent 的本地优先工作台。

## 开发启动

后端依赖安装：

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
```

启动本地 API（默认 `127.0.0.1:8000`，会自动打开浏览器）：

```bash
.venv/bin/novelagent --host 127.0.0.1 --port 8000
```

开发前端：

```bash
cd frontend
npm install
npm run dev
```

运行测试：

```bash
.venv/bin/pytest -q
```

检查项目文件与 SQLite/派生投影一致性：

```bash
.venv/bin/novelagent-fsck /path/to/novel
```

技术选型和抽取边界见 [docs/技术栈与抽取规则.md](docs/技术栈与抽取规则.md)，整体领域架构见 [docs/架构说明.md](docs/架构说明.md)。

开发规则和编码完成后的强制自检见 [AGENTS.md](AGENTS.md)。
