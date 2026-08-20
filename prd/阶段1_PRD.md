# 阶段 1 PRD：正典存储与篇章骨架（定稿）

## 一、阶段目标

在阶段 0（工程基线与目录边界）已完成的基础上，建立可靠的正典存储层和篇章骨架，使作者可以创建小说、卷（Volume）、章节（Chapter）和场景（Scene）。
每个场景拥有不可变的版本历史，正文同时保存为 Markdown 文件并与 SQLite 版本记录双向校验，支持篇章树展示与状态机约束。

---

## 二、数据模型规范

### 2.1 新增 Volume 模型
```python
class Volume(Base):
    __tablename__ = "volumes"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    sequence: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default="IDEA")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
```

### 2.2 Chapter 模型调整
- 新增 `volume_id: Mapped[Optional[int]] = mapped_column(ForeignKey("volumes.id"), nullable=True, index=True)`（支持卷可选）。
- 新增 `contract: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)`（存储 `ChapterContract`，不重复存储 status）。

### 2.3 Scene 模型调整
- 新增 `entry_contract: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)`（存储 `SceneEntryContract`）。
- 新增 `exit_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)`（存储最新已采纳版本的 `SceneExitState`）。

### 2.4 Alembic 迁移脚本
新增 `alembic/versions/0002_add_volume_and_contracts.py`：
- 创建 `volumes` 表；
- `chapters` 表增加 `volume_id` 和 `contract` 列；
- `scenes` 表增加 `entry_contract` 和 `exit_state` 列。

---

## 三、契约结构定义

### 3.1 ChapterContract
```json
{
  "chapter_id": 1,
  "title": "第一章",
  "goal": "引入主角和核心冲突",
  "scene_ids": [1, 2, 3],
  "target_word_count": 5000
}
```

### 3.2 SceneEntryContract
```json
{
  "scene_id": 2,
  "inherits_from_scene_id": 1,
  "time_jump": "CONTINUOUS",
  "location": "客栈大厅",
  "pov_character": "林舟",
  "inherited_state": {
    "characters_present": ["林舟", "沈砚"],
    "active_goal": "寻找失踪的师兄",
    "emotional_tone": "紧张"
  }
}
```

### 3.3 SceneExitState
```json
{
  "scene_id": 1,
  "revision_id": 5,
  "last_action": "林舟决定离开客栈",
  "characters_present": ["林舟"],
  "location": "客栈门口",
  "emotional_tone": "决意",
  "open_threads": ["师兄失踪之谜"],
  "next_scene_hints": ["前往城北旧宅"]
}
```

---

## 四、状态机转换规则

### 4.1 章节状态机
`IDEA -> OUTLINED -> IN_PROGRESS -> READY_FOR_REVIEW -> RELEASED`
`                       \-> LOCALLY_STALE`

| 当前状态 | 允许流转的目标状态 | 前置条件 |
| :--- | :--- | :--- |
| `IDEA` | `OUTLINED` | 无 |
| `OUTLINED` | `IN_PROGRESS`, `IDEA` | 无 |
| `IN_PROGRESS` | `READY_FOR_REVIEW`, `LOCALLY_STALE` | 至少有一个场景处于 `SCENE_ACCEPTED` |
| `READY_FOR_REVIEW` | `RELEASED`, `IN_PROGRESS` | 所有场景均须处于 `SCENE_ACCEPTED` 才能进入 `RELEASED` |
| `LOCALLY_STALE` | `IN_PROGRESS`, `READY_FOR_REVIEW` | 无 |
| `RELEASED` | `IN_PROGRESS`（打回重修） | 需明确解除发布 |

### 4.2 场景状态机
`PLANNED -> WRITING -> PARTIALLY_ACCEPTED -> SCENE_ACCEPTED`
`                    \-> EXTRACTION_PENDING`

| 当前状态 | 允许流转的目标状态 | 前置条件 |
| :--- | :--- | :--- |
| `PLANNED` | `WRITING` | 无 |
| `WRITING` | `PARTIALLY_ACCEPTED`, `SCENE_ACCEPTED`, `EXTRACTION_PENDING` | 需有正文内容 |
| `PARTIALLY_ACCEPTED` | `WRITING`, `SCENE_ACCEPTED`, `EXTRACTION_PENDING` | 无 |
| `EXTRACTION_PENDING` | `SCENE_ACCEPTED`, `WRITING` | 阶段 4 抽取完成后流转 |
| `SCENE_ACCEPTED` | `WRITING`（重新编辑） | 创建新补丁/版本时触发 |

---

## 五、API 接口规范

所有接口均强制校验当前项目上下文与目录白名单权限。

### 5.1 卷管理
- `GET /api/projects/current/volumes`：获取当前项目所有卷，按 `sequence` 排序。
- `POST /api/projects/current/volumes`：创建新卷，自动赋予 `sequence = max + 1`。
- `PUT /api/volumes/{volume_id}`：更新卷标题、状态。
- `DELETE /api/volumes/{volume_id}`：删除卷。若卷下有章节则拒绝删除并返回 `400`。

### 5.2 章节管理
- `POST /api/projects/current/chapters`：创建章节，可指定 `volume_id`，默认 `sequence = 同级 max + 1`。
- `GET /api/chapters/{chapter_id}`：获取单个章节详情、契约及包含的场景列表。
- `PUT /api/chapters/{chapter_id}`：更新章节标题、`volume_id`、`contract`。
- `POST /api/chapters/{chapter_id}/status`：变更章节状态，校验状态机规则。
- `DELETE /api/chapters/{chapter_id}`：删除章节。若章节下有场景或状态为 `RELEASED` 则拒绝删除并返回 `400`。

### 5.3 场景管理
- `POST /api/chapters/{chapter_id}/scenes`：在指定章节下创建场景。
- `GET /api/scenes/{scene_id}`：获取场景详情、当前正文、契约与退出状态。
- `PUT /api/scenes/{scene_id}`：更新场景标题、`pov`、`location`。
- `POST /api/scenes/{scene_id}/status`：变更场景状态，校验状态机规则。
- `GET /api/scenes/{scene_id}/revisions`：获取场景的历史版本列表元数据。
- `GET /api/scenes/{scene_id}/revisions/{revision_id}`：获取指定历史版本的完整正文与元数据。
- `PUT /api/scenes/{scene_id}/entry-contract`：更新 `SceneEntryContract`。
- `PUT /api/scenes/{scene_id}/exit-state`：更新 `SceneExitState`。
- `DELETE /api/scenes/{scene_id}`：删除场景。

### 5.4 篇章树与重排序
- `GET /api/projects/current/tree`：一次性获取完整的 卷 -> 章 -> 场景 嵌套树结构。
- `PUT /api/projects/current/reorder`：
  - Body: `{"type": "volume" | "chapter" | "scene", "parent_id": int | null, "order": [id1, id2, ...]}`
  - 在单一事务内批量更新顺序，如包含非法 ID 或跨容器越权则整体回滚并返回 `400`。

---

## 六、正文文件存储与 CommitJournal / fsck 机制

### 6.1 物理存储结构
```text
{project_dir}/.novelagent/
├── project.db
└── text/
    └── scenes/
        └── scene-{scene_id}/
            ├── current.md                     # 当前最新采纳版本的阅读/预览副本
            ├── rev-{revision_id_1}.md         # 不可变的历史版本 1
            └── rev-{revision_id_2}.md         # 不可变的历史版本 2
```

### 6.2 采纳与写入流程
采纳场景版本时（`POST /api/scenes/{scene_id}/revisions/{revision_id}/accept`）：
1. 在 SQLite 事务内：
   - 验证 `base_revision_id == scene.current_revision_id`；
   - 更新 `scene.current_revision_id = revision.id`，状态置为 `SCENE_ACCEPTED`；
   - 创建 `CommitJournal` 记录，`file_path` 固定指向不可变版本文件 `{project_dir}/.novelagent/text/scenes/scene-{scene_id}/rev-{revision_id}.md`，`content_hash = sha256(content)`；
2. 事务提交后：
   - 写入版本文件 `rev-{revision_id}.md` 并同步更新 `current.md`；
   - 标记 `CommitJournal.file_status = "COMMITTED"`。

### 6.3 崩溃自愈与 fsck
- `novelagent-fsck` 遍历 `CommitJournal`：
  - 检查每个 `rev-{revision_id}.md` 是否存在且 SHA-256 与 `content_hash` 一致；
  - 若文件缺失但 SQLite 中存在 `SceneRevision`，自动重新生成缺失文件；
  - 若哈希不匹配，报告异常并阻断静默覆盖。

---

## 七、验收条件

| 编号 | 验收项 | 验证方式 |
| :--- | :--- | :--- |
| **AC-1** | 场景版本不可变 | `SceneRevision` 不提供修改接口，只能新增 |
| **AC-2** | 完整篇章骨架 CRUD | 卷、章、场景能够正确创建、读取、更新、排序与受控删除 |
| **AC-3** | 批量重排序事务性 | 排序操作在单事务内完成，非法输入整体回滚 |
| **AC-4** | 状态机校验生效 | 非法状态转换返回 `400 Bad Request` 并给出明确错误信息 |
| **AC-5** | 文件与 DB 双向一致 | 版本采纳生成不可变版本文件，`novelagent-fsck` 校验 100% 通过 |
| **AC-6** | 历史版本可回溯 | 可通过 API 查询任意历史版本的正文与元数据 |
