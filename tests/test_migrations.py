from pathlib import Path
from alembic import command
from alembic.config import Config


def test_alembic_upgrade_downgrade(tmp_path: Path):
    db_file = tmp_path / "test_migration.db"
    ini_path = Path(__file__).parent.parent / "alembic.ini"

    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")

    # Test upgrade to head
    command.upgrade(cfg, "head")

    # Test downgrade to base
    command.downgrade(cfg, "base")

    # Test re-upgrade to head
    command.upgrade(cfg, "head")
