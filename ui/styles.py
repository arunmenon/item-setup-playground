# styles.py

def get_css():
    return """
    <style>
        /* General page style */
        body {
            font-family: Arial, sans-serif;
            background-color: #F8F9FA;
            color: #333;
        }
        
        /* Title and headers */
        .title {
            color: #003366;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 0.5em;
        }

        .subheader {
            color: #00509E;
            font-size: 1.5em;
            margin-top: 1em;
        }

        /* Input box styling */
        .stTextInput > div > input, .stTextArea textarea {
            border: 1px solid #CED4DA;
            border-radius: 8px;
            padding: 10px;
        }

        /* Button styling */
        button {
            background-color: #007BFF !important;
            color: white !important;
            border-radius: 5px;
            padding: 10px 15px;
            font-weight: bold;
        }

        /* Response box styling */
        .response-box {
            background-color: #E9ECEF;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 1rem;
            box-shadow: 0 0 8px rgba(0, 0, 0, 0.1);
            color: #333;
        }

        /* Leaderboard styling */
        .leaderboard-table {
            margin-top: 20px;
        }
    </style>
    """
