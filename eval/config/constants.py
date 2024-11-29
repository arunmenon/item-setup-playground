# File: eval/config/constants.py

# API URL for enrichment requests
API_URL = "http://10.56.16.163:5001/enrich-item"
#API_URL = "http://0.0.0.0:5001/enrich-item"

# Mapping of tasks to their enhancement types
TASK_MAPPING = {
    'title': 'title_enhancement',
    'short_description': 'short_description_enhancement',
    'long_description': 'long_description_enhancement'
}
