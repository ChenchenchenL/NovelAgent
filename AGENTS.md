# NovelAgent 开发规则

本文件是仓库级开发规则。所有代码、配置、迁移、测试和前端变更都必须遵守本文件。

“必须”“禁止”“不得”属于强制约束。除非明确说明，否则不得绕过。

---

## 一、任务开始前必须读取

每次开始开发任务，必须按以下顺序读取：

1. `README.md`：启动方式、测试命令和项目入口。
2. `docs/README.md`：文档索引和设计基准。
3. `docs/架构说明.md`：领域边界、正典/工作区边界、连续性模型和架构不变量。
4. `docs/技术栈与抽取规则.md`：技术选型、事实模态、抽取字段和自动确认规则。
5. `docs/功能需求.md`：当前实现状态、功能范围、优先级和验收基线。
6. `docs/开发顺序.md`：当前阶段、开发依赖和禁止提前开发的能力。
7. 与任务直接相关的代码、测试、迁移和配置。

如果任务涉及数据库，额外读取：

* `backend/novelagent/models.py`
* `backend/novelagent/db.py`
* `alembic/versions/`

如果任务涉及 API，额外读取：

* `backend/novelagent/api.py`
* `backend/novelagent/schemas.py`
* 相关 Router、Service 和测试。

如果任务涉及前端，额外读取：

* `frontend/src/`
* `frontend/package.json`
* `frontend/vite.config.js`
* 相关组件、Hooks、API Client 和测试。

发现文档与代码冲突时，先确认当前正确基线，并同步修正文档、代码和测试，不得只修改其中一处。

---

# 二、核心编程规则

## 2.1 领域和数据边界

* 作者确认正文是文学表达的首要来源；抽取候选、模型输出、向量、KG、摘要和缓存不得自动成为正典。
* 所有生成先进入工作区，只有作者决议或明确的正典命令才能提交。
* Scene 是生成、检查和局部提交的主要粒度；Chapter 是组织和发布聚合。
* 物品、人物身份、地点移动、关系、剧情和伏笔必须有明确对象、来源、版本和状态，不得使用无来源标签数组代替。
* `ACTUAL` 之外的事实模态不得直接参加物理世界硬冲突；低置信 LLM 抽取不能直接阻断正文保存。
* 模型没有直接数据库写权限，只能返回经过 Schema 校验的候选，由领域服务负责授权、校验和提交。
* 派生索引必须可从正典重建；索引损坏或落后时回退正典，不得伪造强一致结果。

---

## 2.2 技术栈和通用实现规则

* 后端使用 Python 3.11+、FastAPI、Pydantic、SQLAlchemy 2、Alembic。
* 前端使用 React/Vite，保持现有 Markdown 编辑和原文预览方向。
* 数据库访问必须通过统一 Session/事务边界；新增表必须提供 Alembic 迁移。
* API 输入使用 Pydantic Schema，输出不得直接暴露 ORM。
* API 错误必须具有稳定错误类型和可操作信息。
* 长任务使用持久化任务状态和 SSE，不得只保存于进程内存。
* 手工编辑使用 `apply_patch`，不得用 `cat`、临时脚本重写版本控制文件或覆盖用户已有修改。
* 默认使用 ASCII 新增代码和配置；已有中文文档按原文件字符集维护。
* 禁止提交 API Key、Token、个人路径、临时数据库、`node_modules`、`.venv`、构建缓存和日志。

---

## 2.3 代码规模与复杂度

所有新增代码必须遵守：

* 普通函数：≤ 50 行。
* API Handler：≤ 30 行。
* Service 方法：≤ 50 行。
* Domain Rule：≤ 40 行。
* React Component：≤ 120 行。
* 普通代码文件：≤ 300 行。
* 函数圈复杂度原则上 ≤ 10。
* 条件嵌套原则上 ≤ 3 层。
* 普通函数参数 ≤ 4 个。

超过限制必须拆分，不得通过大量注释、空行或压缩代码规避。

拆分应按照**职责、领域和变化原因**进行，不得机械拆分。

---

## 2.4 公共方法和重复代码

* 相同业务逻辑出现 2 次以上，必须检查是否应该抽取。
* 相同领域规则只能有一个权威实现。
* 公共方法必须放在语义明确的包中，并具有明确输入、输出和测试。
* 禁止为了复用而强行抽象不同业务。
* 禁止复制粘贴业务逻辑后只修改变量名。
* 禁止把所有公共代码堆入 `utils.py`、`common.py`、`helpers.py`。
* 没有调用方、没有明确职责或没有测试的抽象不得新增。

---

# 三、后端架构与包管理

后端禁止将所有代码放在 `backend/novelagent/` 根目录。

推荐：

```text
backend/novelagent/
├── api/
│   ├── routers/
│   ├── schemas/
│   └── dependencies.py
├── domain/
│   ├── models/
│   └── rules/
├── application/
│   └── services/
├── infrastructure/
│   ├── db/
│   ├── repositories/
│   ├── storage/
│   └── fsck/
├── integrations/
│   └── model_gateway/
├── config/
└── main.py
```

允许结合项目现有结构调整目录，但必须保持职责边界。

### 包职责

* `api/`：HTTP、Schema、鉴权和错误映射。
* `domain/`：实体、状态机、领域规则和不变量。
* `application/`：业务用例、Service 编排和事务边界。
* `infrastructure/`：数据库、Repository、文件系统和基础设施。
* `integrations/`：LLM、外部 API 和第三方 SDK 适配。
* `config/`：配置和环境变量。
* `main.py`：应用启动和依赖装配。

依赖方向：

```text
API
 ↓
Application
 ↓
Domain

Application
 ↓
Infrastructure / Integrations
```

禁止：

* `Domain → API`
* `Domain → FastAPI`
* `Domain → HTTP`
* `Domain → 外部 IO`
* `Infrastructure → API`
* `Integrations → Application`
* 循环依赖
* 跨包访问私有实现
* 为调用一个方法直接依赖整个上层模块。

一个目录出现多个独立业务领域、文件明显形成业务分组或文件数量持续增长时，必须继续拆包。

禁止建立无法说明职责的万能包。

---

## 3.1 后端分层规范

### API / Transport

职责：

* HTTP 路由；
* 参数校验；
* 鉴权；
* 调用 Application Service；
* Response 转换；
* HTTP 状态码映射。

禁止：

* 复杂业务逻辑；
* 直接写 SQL；
* 直接操作 ORM；
* 直接操作文件；
* 拼接复杂 Prompt；
* 管理复杂事务。

API Handler 应保持：

```text
请求 → 校验 → 鉴权 → Service → Response
```

### Domain

职责：

* 领域实体；
* Value Object；
* 状态转换；
* 领域规则；
* 领域不变量。

必须尽量保持纯 Python，可独立测试。

禁止依赖：

* FastAPI；
* HTTP；
* 文件系统；
* 外部 API；
* LLM；
* 环境变量。

### Application Service

职责：

* 业务用例；
* 跨领域编排；
* 事务边界；
* 协调 Domain、Repository、Storage、Model Gateway。

Service 不得成为包含所有业务的“万能 Service”。

### Infrastructure

职责：

* 数据库；
* Repository；
* 文件系统；
* SQLite；
* WAL；
* fsck；
* 存储适配。

Infrastructure 不得决定领域业务规则。

### Model Gateway / Integrations

职责：

* OpenAI-compatible LLM；
* T0/T1/T2/T3 模型路由；
* Token 预算；
* Timeout；
* Retry；
* Provider 错误转换；
* 调用指标。

禁止：

* 直接写数据库；
* 修改正典；
* 提交作者决议；
* 执行领域授权。

---

# 四、前端架构与包管理

前端禁止所有组件、Hooks、API 和工具全部放在 `frontend/src/` 根目录。

推荐：

```text
frontend/src/
├── pages/
├── components/
├── features/
│   ├── project/
│   ├── chapter/
│   ├── scene/
│   └── generation/
├── hooks/
├── api/
├── services/
├── stores/
├── types/
├── utils/
└── app/
```

### 包职责

* `pages/`：页面级组件。
* `components/`：跨业务复用 UI。
* `features/`：具体业务领域。
* `hooks/`：可复用状态和副作用。
* `api/`：后端 API Client。
* `services/`：前端业务服务。
* `stores/`：全局状态。
* `types/`：公共类型。
* `utils/`：真正通用且无业务语义的工具。

业务代码优先放在 `features/<domain>/`，不得全部堆入 `components/`。

例如：

```text
features/scene/
├── components/
├── hooks/
├── api.ts
├── types.ts
└── utils.ts
```

---

## 4.1 前端组件规范

* Component 遵循单一职责。
* Component 主要负责 UI 和用户交互。
* API 请求放入 `api/` 或对应 Feature API。
* 复杂状态和副作用必须抽取 Hook。
* 复杂数据转换必须抽取独立函数。
* 不得在多个组件复制同一份正典状态。
* UI 组件与业务逻辑必须分离。
* Component 超过 120 行必须拆分。
* 禁止组件之间直接修改彼此内部状态。

---

## 4.2 状态管理

必须区分：

**Server State：**

```text
projects
chapters
scenes
revisions
generation_tasks
```

**Local UI State：**

```text
selected_tab
expanded_nodes
dialog_open
draft_content
cursor_position
```

正典状态以服务端为准，不得通过多个本地副本形成新的事实来源。

---

# 五、前后端接口与通信契约

## 5.1 Schema

* 前后端通信必须基于明确 Request/Response Schema。
* 禁止直接暴露 ORM。
* 新增字段默认保持向后兼容。
* 修改字段语义时必须同步更新 Schema、测试、前端和文档。
* 外部模型返回结果必须经过 Schema 校验。

## 5.2 错误

统一错误结构：

```json
{
  "detail": "可操作的错误说明"
}
```

HTTP 状态：

* `400`：参数/状态非法；
* `401`：未授权；
* `403`：越权；
* `404`：不存在；
* `409`：版本冲突；
* `422`：Schema 验证失败；
* `500`：服务内部错误；
* `503`：外部依赖不可用。

前端不得根据错误文案判断业务状态，应使用稳定错误码/错误类型。

## 5.3 长任务

生成、批量导入等耗时任务采用：

```text
REST 创建任务
 ↓
持久化 Task
 ↓
后台执行
 ↓
SSE
 ↓
前端订阅
```

必须支持：

* task_id；
* 持久化状态；
* 取消；
* 超时；
* 重试；
* 服务重启恢复；
* SSE 断线重连；
* 重复事件；
* 最终状态查询。

前端不得自行判断任务最终成功。

---

# 六、配置、依赖和硬编码

## 6.1 配置

Endpoint、模型名、Token 预算、Timeout、Retry、路径、端口和质量阈值必须集中配置。

禁止在业务代码中散落相同配置。

禁止硬编码：

* API Key；
* Token；
* Provider 凭据；
* 用户目录；
* 开发机绝对路径。

协议常量、状态机常量和明确领域不变量可以常量化。

---

## 6.2 第三方依赖

新增依赖必须：

1. 先检查现有依赖是否已有相同能力。
2. 能用标准库解决时不新增依赖。
3. 说明新增依赖用途。
4. 区分生产依赖和开发/测试依赖。
5. 更新项目规定的依赖文件和 Lockfile。
6. 删除未使用依赖。
7. 升级依赖后执行完整测试。

后端依赖统一通过项目规定的 `pyproject.toml`、`requirements.txt` 等文件管理。

前端依赖统一通过：

```text
package.json
package-lock.json
```

管理。

禁止依赖只存在于本地环境而未写入依赖文件。

禁止为了一个很小的功能引入大型或重复依赖。

---

# 七、错误、事务和安全

* Domain 层不得抛 `HTTPException`。
* API 层负责 HTTP 错误映射。
* 禁止 `except Exception: pass`。
* 禁止吞掉异常后返回伪成功。
* 正典写入、Scene 版本和作者决议必须在明确事务边界内完成。
* 外部模型调用不得放入正典事务。
* 所有重试必须具有幂等键或可证明的幂等效果。
* 文件、SQLite 和派生索引必须可由 `CommitJournal`、`PendingProjection`、`fsck` 检测和恢复。
* 所有用户路径必须进行路径遍历检查。
* 所有资源权限必须由后端重新验证。
* 日志不得包含 API Key、Cookie、完整正文、完整 Prompt、ContextPack 和敏感路径。

---

# 八、代码规范

后端遵循：

* PEP 8；
* PEP 257；
* 类型标注；
* 项目配置的 Ruff/Lint 规则。

前端遵循：

* 项目现有 ESLint/TypeScript 规则；
* 优先使用明确类型；
* 禁止使用 `any` 隐藏类型问题；
* 公共函数和 API 类型必须明确。

命名必须表达业务含义。

禁止大量使用：

```text
data
obj
tmp
result
helper
process
do_work
```

Boolean 优先使用：

```text
is_*
has_*
can_*
should_*
```

禁止：

```python
try:
    ...
except Exception:
    pass
```

禁止通过 `None`、空数组或默认值隐藏真实错误。

---

# 九、测试要求

* 每个新领域规则先写失败测试，再实现。
* 数据模型变更必须测试 Migration、旧数据读取和兼容性。
* API 变更必须覆盖成功、未授权、输入错误、越权、版本冲突、重复请求和依赖失败。
* 长文本、Unicode、空值、重复事件、断线、超时、取消、损坏文件和投影滞后必须有边界测试。
* 前端变更至少执行生产构建；涉及交互时增加浏览器/API 冒烟验证。
* 测试不得依赖开发机绝对路径、当前时间、随机顺序或外部网络。

---

# 十、标准开发流程

1. 读取本文件和全部必读文档，确认当前开发阶段。
2. 检查 `git status`，保留用户已有修改。
3. 明确领域对象、写入边界、配置项、失败语义和测试范围。
4. 明确新增代码所属架构层和包。
5. 检查依赖方向，避免循环依赖。
6. 先更新/新增测试，再实现最小变更。
7. 检查函数、文件、组件和复杂度是否超限。
8. 检查是否存在重复代码或可复用的公共方法。
9. 数据库变更同时更新模型、迁移、初始化路径和测试。
10. API 变更同时更新 Schema、前端调用、错误处理和文档。
11. 前端变更同时检查 Component、Hook、API Client 和状态边界。
12. 运行测试、Lint、语法检查和前端构建。
13. 执行第十一节六项自检。
14. 最终输出变更摘要、验证命令、验证结果、未完成项和残余风险。

---

# 十一、编码完成后的强制六项自检

每次编码任务完成后，必须逐项检查并在交付说明中报告“通过/发现问题/不适用”。

## 11.1 隐藏 BUG 检查

检查：

* 空值、边界值、超长正文、Unicode；
* 重复请求、并发编辑、陈旧版本；
* 异常重试、服务重启；
* 模型超时、限流、乱序、部分输出、错误 Schema；
* 事务提交前失败、提交后文件失败、索引失败；
* 恢复重复执行。

执行：

```bash
.venv/bin/pytest -q
.venv/bin/python -m py_compile backend/novelagent/*.py tests/*.py
```

## 11.2 代码边界清晰检查

确认：

* API 不直接实现领域规则；
* Domain 不依赖 FastAPI/IO；
* Model Gateway 不直接写正典；
* Repository 不做业务决策；
* 正典、工作区、派生索引和前端状态没有越权读写；
* 没有循环依赖；
* 没有跨模块私有实现引用；
* 前端没有裸调 `fetch`；
* 没有超大文件或超大 Component。

数据库变更执行 Alembic Migration 并验证新旧数据读取。

## 11.3 冗余设计检查

检查：

* 重复状态枚举；
* 重复 Schema；
* 重复查询；
* 重复序列化；
* 重复错误映射；
* 重复模型配置；
* 重复权限/路径校验；
* 重复数据转换；
* 重复 SSE 逻辑。

合并真正相同的业务规则，但不得为了复用混合不同一致性边界。

删除没有调用方、没有测试或没有明确扩展点的抽象。

## 11.4 不合理硬编码检查

执行：

```bash
rg -n "api[\_-]?key|token|https?://|/home/|localhost|127\.0\.0\.1|timeout|retry|model" backend frontend tests
```

确认命中项属于：

* 协议常量；
* 测试夹具；
* 集中配置默认值；
* 明确领域不变量。

否则必须移入配置。

## 11.5 日志覆盖检查

必须覆盖且可关联：

* 启动/关闭；
* 目录授权；
* 项目切换；
* 正典提交；
* 版本冲突；
* 生成任务状态；
* 模型调用；
* 抽取任务；
* 导入检查点；
* SSE 断线/恢复；
* Migration；
* fsck；
* 投影重建；
* 不可恢复失败。

日志包含：

```text
task_id
project_id
scene_id
version
status
duration
error_type
```

不得包含：

```text
API Key
Cookie
完整正文
完整 Prompt
完整 ContextPack
敏感本地路径
```

## 11.6 代码健壮性检查

确认：

* 外部依赖不可用时能降级、排队或明确失败；
* 不返回伪成功；
* 写入具备事务、幂等和恢复能力；
* 文件/索引失败可由 `fsck` 发现和修复；
* 任务支持取消、超时、重试和服务重启恢复；
* API 能处理越权资源、版本冲突和损坏输入；
* 前端稳定处理 Loading、Empty、Error、断线和恢复；
* 无未处理 Promise 错误。

---

# 十二、交付自检报告格式

每次完成编码任务，最终说明必须包含：

```text
变更范围：

代码结构：
通过/问题

函数与文件规模：
通过/问题

模块依赖：
通过/问题

公共代码抽取：
通过/问题

第三方依赖：
通过/问题

六项自检：

1. 隐藏 BUG：通过/问题

2. 边界清晰：通过/问题

3. 冗余设计：通过/问题

4. 硬编码：通过/问题

5. 日志覆盖：通过/问题

6. 健壮性：通过/问题

执行的验证命令：

验证结果：

未完成项和残余风险：
```

未完成的自检、失败的测试、超限代码和已知风险不得省略或写成“无问题”。
