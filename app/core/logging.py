
import logging
import sys
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

def setup_logging():
    # Configure Sentry Logging Integration
    sentry_logging = LoggingIntegration(
        level=logging.INFO,        # Capture info and above as breadcrumbs
        event_level=logging.ERROR  # Send errors as events
    )

    # Basic configuration for standard python logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Set external libraries to warning to avoid noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("readability").setLevel(logging.WARNING)
