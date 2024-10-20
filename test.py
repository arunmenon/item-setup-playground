import asyncio
from handlers.llm_handler import BaseModelHandler
from models.llm_request_models import BaseLLMRequest



# Define a function to test the vLLM endpoint on RunPod
async def test_vllm_runpod():
    # Instantiate the handler with the vLLM endpoint
    handler = BaseModelHandler(
        provider="runpod",
        api_key=None,
        api_base="https://api.runpod.ai/v2/vllm-caiqtd1nirhws2/openai/v1",
        model="neuralmagic/Llama-3.2-3B-Instruct-FP8-dynamic",
        max_tokens=1000,
        temperature=0.7
    )

    # Define the prompt to send to the vLLM endpoint
    prompt = "Write a poem on Elon Musk"
    llm_name = "vllm1"
    task = "title_reformulation"

    # Invoke the handler
    try:
        response = await handler.invoke(request=BaseLLMRequest(prompt=prompt), llm_name=llm_name, task=task)
        print(response)
    except BaseException as e:
        print(response)
        print(f"Error during invocation: {str(e)}")

# Run the test if executed as a script
if __name__ == "__main__":
    asyncio.run(test_vllm_runpod())
