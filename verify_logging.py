
import logging
import os

import sentry_sdk

from app.core.logging import setup_logging

# Set dummy DSN to avoid errors if not set
if not os.getenv("SENTRY_DSN"):
    os.environ["SENTRY_DSN"] = "https://examplePublicKey@o0.ingest.sentry.io/0"

def test_logging_setup():
    setup_logging()
    
    logger = logging.getLogger("test_logger")
    logger.info("Test INFO log")
    logger.error("Test ERROR log")
    
    # Check if handlers are configured
    assert logging.getLogger().handlers, "Root logger should have handlers"
    
    print("Logging setup verified.")

def test_sentry_integration():
    sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])
    
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("test_tag", "value")
        # Just ensure no exception is raised
    
    print("Sentry integration verified.")

if __name__ == "__main__":
    test_logging_setup()
    test_sentry_integration()
