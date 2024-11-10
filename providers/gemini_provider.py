# providers/gemini_provider.py
import os
import google.generativeai as genai
import logging
from providers.base_provider import BaseProvider

class GeminiProvider(BaseProvider):

    
    def __init__(self,  model="gemini-1.5-flash"):
        self.logger =  logging.getLogger(self.__class__.__name__)
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.logger.error("Gemini API key is not provided.")
            raise ValueError("Gemini API key is required.")
        genai.configure(api_key=self.api_key)
        self.model_instance = genai.GenerativeModel(model)
   

    def create_chat_completion(self,model:str, messages: list, temperature: float, max_tokens: int):
        try:
            # Prepare the prompt
            prompt = "\n".join([msg['content'] for msg in messages])

            # Generate content
            response = self.model_instance.generate_content(
                contents=prompt,
                safety_settings="BLOCK_ONLY_HIGH",
                generation_config=self.configure_gen_settings(temperature, max_tokens)
            )
            print(response.candidates[0].finish_reason)
            print(response.candidates[0].safety_ratings)
            content = response.text
            return {"choices": [{"message": {"content": content}}]}
        except Exception as e:
            self.logger.error("Error creating Gemini chat completion: %s", str(e))
            raise

    def configure_gen_settings(self, temperature, max_tokens):
        return genai.types.GenerationConfig(
                # Only one candidate for now.
                candidate_count=1,
                
                #stop_sequences=["x"],
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

    