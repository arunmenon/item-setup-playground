from providers.openai_provider import OpenAIProvider
from providers.runpod_provider import RunPodProvider
import logging


class ProviderFactory:
    logger = logging.getLogger(__name__)

    # Set default logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

   


    @staticmethod
    def create_provider(provider: str, api_key: str, api_base: str):
        if provider == "openai":
            ProviderFactory.logger.debug(f"Creating OpenAI provider with api_base: {api_base}")
            return OpenAIProvider(api_key, api_base)
        elif provider == "runpod":
            ProviderFactory.logger.info(f"Creating RunPod provider with api_base: {api_base}")
            return RunPodProvider()
        else:
            ProviderFactory.logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
