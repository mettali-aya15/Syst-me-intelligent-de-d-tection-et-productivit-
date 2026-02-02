from app.db.session import engine
from app.db.base import Base

# Import ALL models here
from app.models.factory import Factory
from app.models.camera import Camera
from app.models.machine import Machine
from app.models.employee import Employee
from app.models.event import Event
from app.models.production import ProductionCount
from app.models.report import DailyReport
from app.models.alert import Alert
from app.models.user import User
from app.core.logger import get_logger

logger = get_logger(__name__)

def init_db():
    logger.info("📦 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database initialized")

# Run manually
# python -c "from app.db.init_db import init_db; init_db()"
