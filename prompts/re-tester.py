import re


template_text_1 = """
Provide your evaluation in the following JSON format:

{
  "quality_score": <0-100>,
  "compliance": <1-5>,
  "clarity": <1-5>,
  "relevance": <1-5>,
  "accuracy": <1-5>,
  "reasoning": {
    "compliance": "<detailed explanation>",
    "clarity": "<detailed explanation>",
    "relevance": "<detailed explanation>",
    "accuracy": "<detailed explanation>"
  },
  "suggestions": "<specific suggestions for improvement or 'None' if the title is excellent>"
}

Product Title:
{response_content}

Style Guide:
{styling_guide}
"""

template_text_2 = """
Dear {customer_name},

Your order {order_id} has been shipped.

Thank you,
{company_name}
"""

def extract_placeholders(template_text):
    # This regex matches {placeholder} where placeholder is a word (letters, numbers, or underscores)
    placeholders = re.findall(r"{([a-zA-Z0-9_]+)}", template_text)
    placeholders = list(set(placeholders))  # Remove duplicates
    placeholders_str = ', '.join(placeholders)
    return placeholders_str

placeholders = extract_placeholders(template_text_1)
print(placeholders)  # Output: 'response_content, styling_guide'
placeholders = extract_placeholders(template_text_2)
print(placeholders)  # Output: 'response_content, styling_guide'
