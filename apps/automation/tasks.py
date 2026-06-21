import logging
from apps.automation.services import (
    run_fee_reminders,
    check_low_attendance,
    run_upcoming_exam_alerts,
)

logger = logging.getLogger("crm.automation.tasks")

try:
    from celery import shared_task
except ImportError:
    # Safe fallback dummy decorator if celery is not installed in current env
    def shared_task(func):
        return func


@shared_task
def run_fee_reminders_task():
    logger.info("Starting run_fee_reminders_task Celery execution")
    return run_fee_reminders()


@shared_task
def check_low_attendance_task():
    logger.info("Starting check_low_attendance_task Celery execution")
    return check_low_attendance()


@shared_task
def run_upcoming_exam_alerts_task():
    logger.info("Starting run_upcoming_exam_alerts_task Celery execution")
    return run_upcoming_exam_alerts()
