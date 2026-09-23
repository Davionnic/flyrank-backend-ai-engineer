import logging
import sys
from app.database import SessionLocal
from app.services.reconciliation_service import ReconciliationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("background_worker")


def run_worker_tasks():
    logger.info("Background Worker started.")
    db = SessionLocal()
    try:
        # Task 1: Check Quota Thresholds and Alerts (80% / 100%)
        logger.info("Executing Task 1: Quota Threshold Inspection...")
        alerts = ReconciliationService.check_usage_alerts(db)
        logger.info(f"Quota threshold check complete. Alerts triggered: {len(alerts)}")

        # Task 2: Reconcile Stripe Subscriptions against Stripe truth
        logger.info("Executing Task 2: Stripe Subscription Reconciliation...")
        rec_result = ReconciliationService.reconcile_stripe_subscriptions(db)
        logger.info(f"Reconciliation result: {rec_result}")

        logger.info("Background tasks completed successfully.")
    except Exception as e:
        logger.error(f"[WORKER CRITICAL FAILURE] Unexpected error in background job: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_worker_tasks()

