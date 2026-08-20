from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from novelagent.domain.models import Chapter, GenerationWorkspace, Project, Scene, SceneRevision


def test_alembic_upgrade_downgrade(tmp_path: Path):
    db_file = tmp_path / "test_migration.db"
    ini_path = Path(__file__).parent.parent / "alembic.ini"

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")

    # Test upgrade to head
    command.upgrade(cfg, "head")

    # Test ORM operations on real migrated database
    engine = create_engine(f"sqlite:///{db_file}")
    with Session(engine) as session:
        project = Project(path=str(tmp_path), name="测试项目")
        session.add(project)
        session.flush()

        chapter = Chapter(project_id=project.id, title="第1章", sequence=1)
        session.add(chapter)
        session.flush()

        scene = Scene(chapter_id=chapter.id, title="第1场", sequence=1)
        session.add(scene)
        session.flush()

        rev = SceneRevision(
            scene_id=scene.id,
            content="正文",
            source="AUTHOR",
            content_hash="dummy_hash",
            patch_info={"intent": "edit"},
        )
        session.add(rev)
        session.flush()

        ws = GenerationWorkspace(
            scene_id=scene.id,
            base_revision_id=rev.id,
            draft_content="草稿正文",
            cursor_position=2,
            undo_stack=[{"text": "旧"}],
            redo_stack=[],
            auto_save_snapshot={"draft_content": "草稿正文"},
        )
        session.add(ws)
        session.commit()

        # Query back
        queried_ws = session.get(GenerationWorkspace, ws.id)
        assert queried_ws is not None
        assert queried_ws.draft_content == "草稿正文"
        assert queried_ws.cursor_position == 2

    # Test downgrade to base
    command.downgrade(cfg, "base")

    # Test re-upgrade to head
    command.upgrade(cfg, "head")
