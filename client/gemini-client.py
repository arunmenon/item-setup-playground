import google.generativeai as genai
import os

# Configure the API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Define the model and prompt
model = genai.GenerativeModel("gemini-1.5-flash")
prompt = prompt = """You are an assistant tasked with enhancing product titles. Use all input information provided below to create a clear, concise, and informative title.

			Original Title:
			Classic Leather Oxford Shoes

			Short Description:
			Timeless leather Oxford shoes for formal and casual wear.

			Long Description:
			Our Classic Leather Oxford Shoes are designed to offer both elegance and comfort. Made from high-quality full-grain leather, they are perfect for both office attire and weekend outings.

			Instructions:
			- Follow the styling guidelines provided here:
			Casual & Dress Shoes Product Title Enhancement Guidelines
			Enhance product titles for Casual & Dress Shoes by following these guidelines. Ensure the final title is clear, concise, and includes all necessary information.
			Title Construction:
			Sequence:
			1. Brand or License Name (include if applicable)
			2. Shoe Category (must be included)
			3. Footwear Feature (include if applicable)
			4. Casual & Dress Shoe Style (must be included)
			5. Attributes: Shoe Width Style / Heel Height Style / Shoe Heel Style / Toe Style (include up to 3 applicable attributes, separated by commas)
			6. Color (include if applicable)
			7. Shoe Size (include if applicable, separated by a comma)

			Guidelines:

			- Brand or License Name
			  - Include if applicable.
			  - Examples: Dockers, Clarks, Nike

			- Shoe Category
			  - Must be included.
			  - Use "Men's," "Women's," "Unisex," or "Unisex Kids" as appropriate.
			  - Examples: Men's Dress Shoe, Women's Casual Shoe

			- Footwear Feature
			  - Include if applicable.
			  - Examples: Waterproof, Slip-Resistant, Lightweight

			- Casual & Dress Shoe Style
			  - Must be included.
			  - Examples: Oxford, Loafer, Derby, Brogue

			- Shoe Width Style / Heel Height Style / Shoe Heel Style / Toe Style
			  - Include up to 3 attributes to describe style, fit, and features, separated by commas.
			  - Examples:
			    - Shoe Width Style: Wide, Narrow
			    - Heel Height Style: Low Heel, High Heel
			    - Shoe Heel Style: Block Heel, Stiletto
			    - Toe Style: Round Toe, Pointed Toe

			- Color
			  - Include if applicable.
			  - If multiple colors, list with "&".
			  - Example: Black, Red & White

			- Shoe Size
			  - Include if applicable.
			  - Precede with a comma.
			  - Examples: Size 10, Sizes 6-9

			- Gender Formatting
			  - Use "Men's," "Women's," or "Unisex."
			  - For both Men's and Women's, use "Unisex."
			  - For both Boys and Girls, use "Unisex Kids."
			  - Omit the term "Regular."

			Examples:
			1. With Brand and Multiple Attributes:
			   - Dockers Men's Dress Oxford Shoe, Wide & Cap Toe, Black, Size 10
			2. With License Name and Features:
			   - Marvel Women's Casual Loafer, Slip-Resistant, Red & White, Sizes 6-9
			3. With Multiple Styles and Features:
			   - Clarks Unisex Derby Shoe, Waterproof & Lightweight, Brown
			4. Minimal Elements:
			   - Men's Dress Oxford Shoe, Black

			Please provide the enhanced title in the following JSON format:
			{"enhanced_title": "Your Enhanced Title Here"}
			"""

# Generate content
response = model.generate_content(
    contents=prompt,
    generation_config=genai.types.GenerationConfig(
        candidate_count=1,
        max_output_tokens=500,
        temperature=0.0,
    ),
)

print(response.text)
