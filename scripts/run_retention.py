import sys
import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.retention_service import RetentionService

# Load environment variables
load_dotenv()

def setup_sentry():
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            send_default_pii=True,
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
            ]
        )
        print("Sentry initialized.")
    else:
        print("Sentry DSN not found. Skipping Sentry initialization.")

def main():
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Setup Sentry
    setup_sentry()

    logger = logging.getLogger(__name__)
    logger.info("Starting file retention cleanup...")

    try:
        service = RetentionService()
        # Parse args for dry-run
        dry_run = "--dry-run" in sys.argv
        service.cleanup_expired_files(dry_run=dry_run)
        logger.info("File retention cleanup finished.")
    except Exception as e:
        logger.error(f"Failed to run retention cleanup: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
