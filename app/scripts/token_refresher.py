"""Background process that keeps the Tempo OAuth tokens alive.

Tempo access tokens (and their refresh tokens) expire after ~30 days. The
refresh token rotates on every refresh, so as long as we refresh *before*
expiry, the token pair keeps renewing indefinitely. This process refreshes
periodically (daily by default) so the application never hits an expired token
during normal operation, and recovers quickly after downtime.

It runs as a separate process alongside uvicorn and Streamlit (see the
Dockerfile CMD). It writes the new tokens back to the shared .env file via
``EnvUpdater``, which is bind-mounted to the host and therefore survives
container restarts.

The interval is configurable through the ``TEMPO_TOKEN_REFRESH_INTERVAL_HOURS``
environment variable (default: 24 hours).
"""

import logging
import os
import time

from reports.helpers import TokenManager, TempoTokenRefreshError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tempo_token_refresher")

REFRESH_INTERVAL_HOURS = float(os.getenv("TEMPO_TOKEN_REFRESH_INTERVAL_HOURS", "24"))
STARTUP_DELAY_SECONDS = 60
RETRY_DELAY_SECONDS = 3600  # Retry one hour later if a refresh fails.


def refresh_once() -> bool:
    """Attempt a single token refresh. Returns True on success."""
    try:
        TokenManager().refresh_access_token()
        logger.info("Tempo access token refreshed successfully.")
        return True
    except TempoTokenRefreshError as exc:
        logger.error(
            "Tempo token refresh failed - a manual OAuth re-authorization is "
            "likely required: %s",
            exc,
        )
        return False
    except Exception as exc:  # network errors, etc. - keep the loop alive
        logger.exception("Unexpected error while refreshing Tempo token: %s", exc)
        return False


def main():
    interval_seconds = REFRESH_INTERVAL_HOURS * 3600
    logger.info(
        "Starting Tempo token refresher (interval=%sh).", REFRESH_INTERVAL_HOURS
    )

    # Let the rest of the app settle before the first refresh.
    time.sleep(STARTUP_DELAY_SECONDS)

    while True:
        succeeded = refresh_once()
        time.sleep(interval_seconds if succeeded else RETRY_DELAY_SECONDS)


if __name__ == "__main__":
    main()
