```markdown
# Item Setup Playground

**Item Setup Playground** is an interactive environment designed for users to input item metadata and evaluate the effectiveness of Large Language Model (LLM) responses across various pre-configured tasks. This platform facilitates the assessment and optimization of LLM-generated content, ensuring high-quality outputs tailored to specific enhancement objectives.

## Table of Contents

- [Project Overview](#project-overview)
- [Project Structure](#project-structure)
  - [Entrypoint](#entrypoint)
  - [Parsers](#parsers)
  - [Prompts](#prompts)
  - [Providers](#providers)
- [Installation](#installation)
- [Running the Entrypoint](#running-the-entrypoint)
- [Configuring Providers](#configuring-providers)
- [Server Logs on Startup](#server-logs-on-startup)
- [License](#license)

## Project Overview

The **Item Setup Playground** empowers users to:

- **Input Item Metadata:** Provide detailed information about items to be processed.
- **Assess LLM Responses:** Evaluate the quality and relevance of responses generated by LLMs for various enhancement tasks.
- **Optimize Tasks:** Refine tasks to improve the efficacy of LLM outputs based on user assessments.

By leveraging a modular architecture, the project ensures scalability, maintainability, and ease of integration with different LLM providers.

## Project Structure

The project is organized into the following directories and files:

```
.
├── README.md
├── __init__.py
├── ae_tasks.csv
├── common/
├── config/
├── entrypoint/
├── exceptions/
├── handlers/
├── models/
├── parsers/
├── performance_test.py
├── prompts/
├── prompts_tasks.csv
├── providers/
├── styling_guides/
└── test.py
```

### Directory and File Descriptions

- **`README.md`**: Comprehensive documentation for the project.
- **`__init__.py`**: Indicates that the directory is a Python package.
- **`ae_tasks.csv`**: Defines various automatic enhancement tasks supported by the playground.
- **`common/`**: Contains shared utilities and helper modules used across the project.
- **`config/`**: Holds configuration files and settings for the application.
- **`entrypoint/`**: Manages the application's entry points and initialization scripts.
- **`exceptions/`**: Defines custom exception classes for robust error handling.
- **`handlers/`**: Contains modules responsible for handling specific tasks or operations.
- **`models/`**: Includes data models and schemas used within the application.
- **`parsers/`**: Houses modules for parsing and interpreting LLM responses.
- **`performance_test.py`**: Script for conducting performance tests to assess application efficiency.
- **`prompts/`**: Stores prompt templates used to interact with LLMs for different tasks.
- **`prompts_tasks.csv`**: Maps prompts to specific enhancement tasks.
- **`providers/`**: Manages integrations with different LLM providers (e.g., OpenAI).
- **`styling_guides/`**: Contains guidelines for formatting and styling LLM responses.
- **`test.py`**: Primary testing script to ensure application functionality.

### Entrypoint

The **`entrypoint/`** directory is the core of the application, responsible for initializing and managing the flow of operations. It contains the main scripts that serve as the starting points for various tasks within the playground.

#### Key Components

- **`main.py`**: The primary script that initializes the application, sets up necessary configurations, and orchestrates the execution of enhancement tasks based on user input.
  - **Responsibilities:**
    - Initializes configuration settings from the `config/` directory.
    - Sets up logging and error handling mechanisms.
    - Invokes appropriate handlers based on user-selected tasks.
    - Manages the interaction between different modules such as parsers, providers, and prompts.
- **`initialize.py`**: Handles the setup processes required before the main application can run, such as loading environment variables and preparing the runtime environment.

#### Workflow

1. **Initialization:** `main.py` starts by invoking `initialize.py` to set up the environment.
2. **Task Selection:** Based on user input, the appropriate handler from the `handlers/` directory is called.
3. **Processing:** The selected handler interacts with parsers and providers to process item metadata and generate LLM responses.
4. **Output:** The final results are compiled and presented to the user for assessment.

## Parsers

The **`parsers/`** directory contains modules dedicated to interpreting and extracting meaningful information from LLM responses. These parsers ensure that the data returned by LLMs is structured and usable for further processing or analysis.

### Key Components

- **`markdown_response_parser.py`**: Parses Markdown-formatted responses from the LLM, extracting specific sections such as enhanced titles, descriptions, and attributes.
  - **Features:**
    - Utilizes regex patterns defined in `patterns_config.txt` to identify and extract relevant content.
    - Employs helper functions mapped in `helper_mapping.txt` to process extracted data.
    - Converts snake_case keys to camelCase for consistency in output.
- **`response_parser.py`**: An abstract base class that defines the interface and common functionalities for all parser implementations.
  - **Features:**
    - Provides methods for loading and compiling regex patterns.
    - Defines the `parse` method that must be implemented by all subclasses.

### Workflow

1. **Pattern Matching:** The parser uses predefined regex patterns to locate specific sections within the LLM's response.
2. **Data Extraction:** Once a pattern matches, the corresponding helper function extracts and processes the data.
3. **Data Structuring:** Extracted data is organized into a structured dictionary, ready for use by other components or for output.

## Prompts

The **`prompts/`** directory stores all the prompt templates used to interact with the LLMs. These prompts are meticulously crafted to guide the LLM in generating responses that are relevant, structured, and aligned with the desired enhancement tasks.

### Key Components

- **`title_enhancement_prompt.txt`**: Template for enhancing item titles.
  - **Structure:**
    - **Instructions:** Clear directives to the LLM on what to generate.
    - **Styling Guide:** Guidelines to ensure the output meets formatting and content quality standards.
    - **Output Format:** Specifies the Markdown structure the LLM should follow.
    - **Example Output:** Provides a sample response to guide the LLM.
- **`short_description_enhancement_prompt.txt`**: Template for enhancing short descriptions.
  - **Similar Structure:** Mirrors the title enhancement prompt but tailored for short descriptions.
- **`long_description_enhancement_prompt.txt`**: Template for enhancing long descriptions.
  - **Comprehensive Instructions:** Detailed guidelines to ensure thorough and descriptive outputs.
- **`attribute_extraction_prompt.txt`**: Template for extracting specific attributes from item metadata.
  - **Focused Extraction:** Directs the LLM to extract only the specified attributes without additional information.
- **`vision_attribute_extraction_prompt.txt`**: Template for extracting vision-related attributes.
  - **Similar to Attribute Extraction:** Tailored for vision-specific data points.

### Workflow

1. **Prompt Selection:** Based on the task (e.g., title enhancement), the corresponding prompt template is selected.
2. **LLM Interaction:** The selected prompt is sent to the LLM provider to generate a response.
3. **Response Handling:** The generated response is then passed to the appropriate parser for extraction and structuring.

## Providers

The **`providers/`** directory manages integrations with various LLM providers, such as OpenAI. This modular approach allows the playground to support multiple providers seamlessly, facilitating flexibility and scalability.

### Key Components

- **`openai_provider.py`**: Handles interactions with the OpenAI API.
  - **Features:**
    - **API Initialization:** Sets up authentication and configuration parameters required to communicate with OpenAI.
    - **Request Handling:** Manages the construction and sending of requests to the OpenAI API based on selected prompts and tasks.
    - **Response Retrieval:** Receives and processes responses from the OpenAI API, making them ready for parsing.
- **`provider_base.py`**: An abstract base class that defines the interface for all LLM providers.
  - **Features:**
    - **Initialization Method:** Ensures that all providers implement necessary setup procedures.
    - **Send Request Method:** Standardizes how requests are sent to different providers.

### Configuring Different Providers

Configuring different LLM providers is straightforward due to the modular architecture. Here's how you can add and configure new providers:

1. **Add Provider Module**
   
   - Navigate to the `providers/` directory.
   - Create a new Python module for the desired provider (e.g., `newprovider.py`).
   - Implement the provider by inheriting from the `ProviderBase` class defined in `provider_base.py`.

   ```python
   # providers/newprovider.py

   from .provider_base import ProviderBase
   import logging

   class NewProvider(ProviderBase):
       def __init__(self, api_key: str):
           super().__init__(api_key)
           logging.info("Initializing NewProvider with provided API key.")

       def send_request(self, prompt: str) -> str:
           # Implement the logic to send a request to the new provider's API
           logging.debug(f"Sending request to NewProvider with prompt: {prompt}")
           response = "NewProvider response based on the prompt."
           return response
   ```

2. **Update Configuration Files**
   
   - Modify the `config/providers_config.json` to include the new provider details.

   ```json
   {
       "providers": [
         {
           "name": "openai",
           "provider": "openai",
           "model": "gpt-4o-mini",
           "temperature": 0
         },
         {
           "name": "runpod_vllm1",
           "provider": "runpod",
           "model": "neuralmagic/Llama-3.2-1B-Instruct-quantized.w8a8",
           "temperature": 0,
           "endpoint_id": "vllm-0avhhxlcsy36tn"
         },
         {
           "name": "runpod_vllm2",
           "provider": "runpod",
           "model": "neuralmagic/Llama-3.2-3B-Instruct-FP8-dynamic",
           "temperature": 0,
           "endpoint_id": "vllm-caiqtd1nirhws2"
         }
       ],
       "tasks": {
         "title_enhancement": {
           "max_tokens": 50
         },
         "short_description_enhancement": {
           "max_tokens": 100
         },
         "long_description_enhancement": {
           "max_tokens": 150
         },
         "attribute_extraction": {
           "max_tokens": 300
         },
         "vision_attribute_extraction": {
           "max_tokens": 500
         }
       }
     }
   ```

3. **Register the Provider**
   
   - Ensure that the `provider_factory.py` is updated to recognize and instantiate the new provider.

   ```python
   # providers/provider_factory.py

   from .openai_provider import OpenAIProvider
   from .newprovider import NewProvider
   from .runpod_provider import RunpodProvider  # Assuming you have a RunpodProvider

   def get_provider(handler_name: str, api_key: str, model: str, temperature: float, endpoint_id: str = None):
       if handler_name.lower() == "openai":
           return OpenAIProvider(api_key, model, temperature)
       elif handler_name.lower() == "runpod":
           return RunpodProvider(api_key, model, temperature, endpoint_id)
       elif handler_name.lower() == "newprovider":
           return NewProvider(api_key, model, temperature)
       else:
           raise ValueError(f"Provider '{handler_name}' is not supported.")
   ```

4. **Use the New Provider**
   
   - When running the playground, specify the desired provider via configuration files or environment variables.

   ```bash
   export PROVIDER_HANDLER_NAME='runpod'
   export RUNPOD_API_KEY='your-runpod-api-key'
   python3 -m entrypoint.main
   ```

### Interaction with Provider Endpoints

The **Item Setup Playground** interacts with LLM provider endpoints through the following process:

1. **Provider Selection:** Based on user configuration or system defaults, the appropriate provider module is selected (e.g., OpenAI, Runpod).
2. **Request Construction:** The provider constructs the request using the selected prompt and item metadata.
3. **LLM Interaction:** The provider sends the request to the LLM API and retrieves the response.
4. **Response Forwarding:** The response is then passed to the parser for extraction and structuring.

This streamlined interaction ensures that the playground remains efficient and responsive, regardless of the underlying LLM provider.

## Installation

Follow these steps to set up the **Item Setup Playground** on your local machine.

### Prerequisites

- **Python 3.8 or higher**: Ensure Python is installed. Download it from [Python's official website](https://www.python.org/downloads/).
- **pip**: Python package installer, typically included with Python installations.
- **Git**: Version control system to clone the repository. Download from [Git's official website](https://git-scm.com/downloads).

### Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/item-setup-playground.git
   cd item-setup-playground
   ```

2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install Dependencies**

   Install the required Python packages using `pip`.

   ```bash
   pip install -r requirements.txt
   ```

   *Note: Ensure that a `requirements.txt` file exists listing all necessary packages. If not, create one based on your project's dependencies.*

4. **Configure Environment Variables**

   Set up necessary environment variables, such as API keys for LLM providers.

   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   export RUNPOD_API_KEY='your-runpod-api-key'
   ```

   *Alternatively, create a `.env` file in the project root and add your configurations there.*

5. **Initialize Configuration Files**

   Ensure that configuration files in the `config/` directory are properly set up. Modify them as needed based on your environment and requirements.

## Running the Entrypoint

To start the **Item Setup Playground**, execute the main entry point script. This initializes the application and prepares it to handle user inputs and process enhancement tasks.

### Steps

1. **Activate the Virtual Environment**

   If not already activated, activate your virtual environment:

   ```bash
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

2. **Run the Main Script**

   Execute the `main.py` script located in the `entrypoint/` directory using the following command:

   ```bash
   python3 -m entrypoint.main
   ```

   *Ensure that you are in the root directory of the project when running this command.*

### Expected Server Logs on Startup

Upon running the entrypoint, the server initializes and logs key events. Below is the actual server log output from a startup session:

```plaintext
python3 -m entrypoint.main
2024-10-30 11:19:05,152 - root - INFO - Logging is configured.
2024-10-30 11:19:05,152 - root - INFO - Configuration loaded from providers/config.json
2024-10-30 11:19:05,152 - root - INFO - Loading all styling guides at application start-up
2024-10-30 11:19:05,152 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loaded styling guides for product types: ['yoga pants', 'hoodies', 'blouses', 'athletic shorts', 't-shirts', 'scarves']
2024-10-30 11:19:05,157 - root - INFO - Loaded styling guides for product types: ['yoga pants', 'hoodies', 'blouses', 'athletic shorts', 't-shirts', 'scarves']
2024-10-30 11:19:05,157 - root - INFO - Starting server on port 5000
INFO:     Started server process [72154]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

### Log Breakdown

- **Logging Configuration:** Indicates that the logging system has been set up.
- **Configuration Loading:** Confirms that configuration settings have been successfully loaded from `providers/config.json`.
- **Styling Guides Loading:** Shows the loading process of styling guides for various product types (`yoga pants`, `hoodies`, `blouses`, `athletic shorts`, `t-shirts`, `scarves`), ensuring that responses adhere to specific formatting and content guidelines.
- **Server Initialization:** Signals the start of the server on the specified port (`5000`) and confirms that the application is up and running, ready to accept user inputs.

### Example Log Flow

1. **Logging Configured:** The application sets up its logging mechanism.
2. **Configuration Loaded:** Essential configurations are loaded from the specified JSON file.
3. **Styling Guides Loaded:** The application loads styling guides for each product type, ensuring consistent and high-quality responses.
4. **Server Started:** The server begins listening on port `5000` and is ready to handle incoming requests.

## Configuring Providers

One of the strengths of the **Item Setup Playground** is its ability to seamlessly integrate with multiple LLM providers. Configuring different providers is straightforward, allowing you to switch or add new providers with minimal effort.

### Provider Configuration Example

Below is the actual `providers_config.json` configuration file located in the `config/` directory. This file defines the available providers and their associated settings, as well as task-specific parameters.

```json
{
    "providers": [
      {
        "name": "openai",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0
      },
      {
        "name": "runpod_vllm1",
        "provider": "runpod",
        "model": "neuralmagic/Llama-3.2-1B-Instruct-quantized.w8a8",
        "temperature": 0,
        "endpoint_id": "vllm-0avhhxlcsy36tn"
      },
      {
        "name": "runpod_vllm2",
        "provider": "runpod",
        "model": "neuralmagic/Llama-3.2-3B-Instruct-FP8-dynamic",
        "temperature": 0,
        "endpoint_id": "vllm-caiqtd1nirhws2"
      }
    ],
    "tasks": {
      "title_enhancement": {
        "max_tokens": 50
      },
      "short_description_enhancement": {
        "max_tokens": 100
      },
      "long_description_enhancement": {
        "max_tokens": 150
      },
      "attribute_extraction": {
        "max_tokens": 300
      },
      "vision_attribute_extraction": {
        "max_tokens": 500
      }
    }
}
```

### Explanation of Configuration Fields

- **`providers`**: An array defining each LLM provider integrated into the playground.
  - **`name`**: A unique identifier for the provider.
  - **`provider`**: The type or service name of the provider (e.g., `openai`, `runpod`).
  - **`model`**: Specifies the model to be used for generating responses.
  - **`temperature`**: Controls the randomness of the LLM's output. A value of `0` makes the output deterministic.
  - **`endpoint_id`** (optional): Specific endpoint identifiers for providers like Runpod, necessary for routing requests to the correct model instance.

- **`tasks`**: Defines the configuration for each enhancement task.
  - **`title_enhancement`**, **`short_description_enhancement`**, etc.: Each key represents a distinct task.
    - **`max_tokens`**: The maximum number of tokens the LLM should generate for the task, controlling the length of the response.

### Adding a New Provider

To add a new LLM provider, follow these steps:

1. **Implement the Provider Module**

   - Create a new Python module in the `providers/` directory (e.g., `newprovider.py`).
   - Inherit from the `ProviderBase` class and implement necessary methods.

   ```python
   # providers/newprovider.py

   from .provider_base import ProviderBase
   import logging

   class NewProvider(ProviderBase):
       def __init__(self, api_key: str, model: str, temperature: float):
           super().__init__(api_key, model, temperature)
           logging.info("Initializing NewProvider with provided API key.")

       def send_request(self, prompt: str) -> str:
           # Implement the logic to send a request to the new provider's API
           logging.debug(f"Sending request to NewProvider with prompt: {prompt}")
           response = "NewProvider response based on the prompt."
           return response
   ```

2. **Update `providers_config.json`**

   - Add a new entry for the provider in the `providers` array.

   ```json
   {
       "name": "newprovider",
       "provider": "newprovider",
       "model": "newmodel-1B",
       "temperature": 0.5,
       "endpoint_id": "newprovider-endpoint-12345"
   }
   ```

3. **Register the Provider in `provider_factory.py`**

   - Ensure that the factory can instantiate the new provider.

   ```python
   # providers/provider_factory.py

   from .openai_provider import OpenAIProvider
   from .runpod_provider import RunpodProvider
   from .newprovider import NewProvider

   def get_provider(handler_name: str, api_key: str, model: str, temperature: float, endpoint_id: str = None):
       if handler_name.lower() == "openai":
           return OpenAIProvider(api_key, model, temperature)
       elif handler_name.lower() == "runpod":
           return RunpodProvider(api_key, model, temperature, endpoint_id)
       elif handler_name.lower() == "newprovider":
           return NewProvider(api_key, model, temperature)
       else:
           raise ValueError(f"Provider '{handler_name}' is not supported.")
   ```

4. **Configure Environment Variables**

   - Set the necessary API keys and other configurations for the new provider.

   ```bash
   export NEWPROVIDER_API_KEY='your-newprovider-api-key'
   ```

5. **Run the Application with the New Provider**

   - Specify the new provider when running the entrypoint.

   ```bash
   python3 -m entrypoint.main
   ```

### Benefits

- **Modularity:** Adding or switching providers does not require significant changes to the core application.
- **Scalability:** Easily extend the playground to support additional providers as needed.
- **Flexibility:** Users can choose their preferred LLM provider based on requirements or availability.

## Server Logs on Startup

Upon running the entrypoint, the server initializes and logs key events. Below is the actual server log output from a startup session:

```plaintext
python3 -m entrypoint.main
2024-10-30 11:19:05,152 - root - INFO - Logging is configured.
2024-10-30 11:19:05,152 - root - INFO - Configuration loaded from providers/config.json
2024-10-30 11:19:05,152 - root - INFO - Loading all styling guides at application start-up
2024-10-30 11:19:05,152 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: yoga pants
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,154 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: hoodies
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: blouses
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,155 - root - INFO - Loading styling guide for product type: athletic shorts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: t-shirts
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loading styling guide for product type: scarves
2024-10-30 11:19:05,156 - root - INFO - Loaded styling guides for product types: ['yoga pants', 'hoodies', 'blouses', 'athletic shorts', 't-shirts', 'scarves']
2024-10-30 11:19:05,157 - root - INFO - Loaded styling guides for product types: ['yoga pants', 'hoodies', 'blouses', 'athletic shorts', 't-shirts', 'scarves']
2024-10-30 11:19:05,157 - root - INFO - Starting server on port 5000
INFO:     Started server process [72154]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

### Log Breakdown

- **Logging Configuration:** Indicates that the logging system has been set up.
- **Configuration Loading:** Confirms that configuration settings have been successfully loaded from `providers/config.json`.
- **Styling Guides Loading:** Shows the loading process of styling guides for various product types (`yoga pants`, `hoodies`, `blouses`, `athletic shorts`, `t-shirts`, `scarves`), ensuring that responses adhere to specific formatting and content guidelines.
- **Server Initialization:** Signals the start of the server on the specified port (`5000`) and confirms that the application is up and running, ready to accept user inputs.

### Example Log Flow

1. **Logging Configured:** The application sets up its logging mechanism.
2. **Configuration Loaded:** Essential configurations are loaded from the specified JSON file.
3. **Styling Guides Loaded:** The application loads styling guides for each product type, ensuring consistent and high-quality responses.
4. **Server Started:** The server begins listening on port `5000` and is ready to handle incoming requests.

## License

This project is licensed under the [MIT License](LICENSE).

---

For any questions or support, please open an issue in the [GitHub repository](https://github.com/yourusername/item-setup-playground/issues).
```