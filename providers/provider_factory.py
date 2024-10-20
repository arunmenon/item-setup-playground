from providers.openai_provider import OpenAIProvider
from providers.runpod_provider import RunPodProvider
import logging


class ProviderFactory:
    logger = logging.getLogger(__name__)

    # Set default logging configuration
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

   


    @staticmethod
    def create_provider(provider_name, **kwargs):
        if provider_name == "openai":
            ProviderFactory.logger.debug(f"Creating OpenAI provider ")
            return OpenAIProvider()
        elif provider_name == "runpod":
            ProviderFactory.logger.info(f"Creating RunPod provider ")
            return RunPodProvider(**kwargs)
        else:
            ProviderFactory.logger.error(f"Unsupported provider: {provider_name}")
            raise ValueError(f"Unsupported provider: {provider_name}")
