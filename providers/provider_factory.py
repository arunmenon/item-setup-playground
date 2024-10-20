from providers.openai_provider import OpenAIProvider
from providers.runpod_provider import RunPodProvider
import logging


class ProviderFactory:
    logger = logging.getLogger(__name__)

    # Set default logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

   


    @staticmethod
    def create_provider(provider: str):
        if provider == "openai":
            ProviderFactory.logger.debug(f"Creating OpenAI provider ")
            return OpenAIProvider()
        elif provider == "runpod":
            ProviderFactory.logger.info(f"Creating RunPod provider ")
            return RunPodProvider()
        else:
            ProviderFactory.logger.error(f"Unsupported provider: {provider}")
            raise ValueError(f"Unsupported provider: {provider}")
