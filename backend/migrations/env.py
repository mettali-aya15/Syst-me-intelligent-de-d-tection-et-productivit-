import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

backend_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_dir))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

try:
    from app.db.base import Base
    
    # Importe TOUS les modèles avec les noms EXACTS
    from app.models.user import User
    from app.models.camera import Camera
    from app.models.employee import Employee
    from app.models.alert import Alert
    from app.models.event import Event
    from app.models.site import Factory
    from app.models.workstation import Machine
    from app.models.production import ProductionCount
    from app.models.report import DailyReport
    
    target_metadata = Base.metadata
    print(f"✅ Modèles importés: {list(Base.metadata.tables.keys())}")
except Exception as e:
    print(f"❌ Erreur: {e}")
    target_metadata = None

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()