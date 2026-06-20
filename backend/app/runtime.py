from app.validation import ValidationStore
from app.reminders import ReminderScheduler, ReminderSender, ReminderStore
from project_config.paths import repo_paths

PATHS = repo_paths()
PROJECT_DIR = PATHS.root
STATIC_DIR = PATHS.static_dir
AUDIO_DIR = PATHS.audio_dir
VISUALS_DIR = PATHS.visuals_dir
DATA_DIR = PATHS.content_dir
VALIDATION_DIR = PATHS.model_dir / "validation"

validation_store = ValidationStore(VALIDATION_DIR)
reminder_store = ReminderStore(VALIDATION_DIR)
reminder_sender = ReminderSender(reminder_store)
reminder_scheduler = ReminderScheduler(reminder_sender)
