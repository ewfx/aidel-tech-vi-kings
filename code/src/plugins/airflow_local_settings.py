from airflow.settings import IS_K8S_OR_K8SCELERY_EXECUTOR
from datetime import timedelta

# Minimum refresh interval in seconds of web interface dag parser
DAGBAG_IMPORT_TIMEOUT = 30

# The frequency (in seconds) that the airflow scheduler should reload DAGs
DAG_REFRESH_INTERVAL = 10  # Reduced to update DAGs quicker

# How many seconds to wait for DAG file processing to deconflict file writes
MIN_FILE_PROCESS_INTERVAL = 1

# For development, reload DAGs on each task heartbeat
if not IS_K8S_OR_K8SCELERY_EXECUTOR:
    MIN_FILE_PROCESS_INTERVAL = 0

# Set a shorter file process interval for faster response to DAG changes
WORKER_REFRESH_INTERVAL = 10  # Reduced to update DAGs quicker