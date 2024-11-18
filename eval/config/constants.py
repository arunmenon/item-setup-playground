# File: eval/config/constants.py

# API URL for enrichment requests
API_URL = "http://localhost:5000/enrich-item"

# Mapping of tasks to their enhancement types
TASK_MAPPING = {
    'title': 'title_enhancement',
    'short_description': 'short_description_enhancement',
    'long_description': 'long_description_enhancement'
}
