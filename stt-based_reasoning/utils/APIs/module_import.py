import dataclasses
import importlib
import os
import sys

module_mapping = {
    "gpt-4": {
        "config_name": "GPT4ConfigClass",
        "module_name": "chatgpt_api",
        "class_name": "ChatGPTAPI",
    },
    "gpt-4-turbo": {
        "config_name": "GPT4Turbo",
        "module_name": "chatgpt_api",
        "class_name": "ChatGPTAPI",
    },
    "gpt-4-o": {
        "config_name": "GPT4O",
        "module_name": "chatgpt_api",
        "class_name": "ChatGPTAPI",
    },
    "gpt-3.5-turbo-16k": {
        "config_name": "GPT35Turbo16kConfigClass",
        "module_name": "chatgpt_api",
        "class_name": "ChatGPTAPI",
    },
    "gpt4all": {
        "config_name": "GPT4ALLConfigClass",
        "module_name": "gpt4all_api",
        "class_name": "GPT4ALLAPI",
    },
    "titan": {
        "config_name": "TitanConfigClass",
        "module_name": "titan_api",
        "class_name": "TitanAPI",
    },
    "azure-gpt-3.5": {
        "config_name": "AzureGPT35ConfigClass",
        "module_name": "azure_api",
        "class_name": "AzureGPTAPI",
    },
    "gemini-1.0": {
        "config_name": "Gemini10ConfigClass",
        "module_name": "gemini_api",  # Assuming you'll create gemini_api.py
        "class_name": "GeminiAPI",  # Assuming class name will be GeminiAPI
    },
    "gemini-1.5": {
        "config_name": "Gemini15ConfigClass",
        "module_name": "gemini_api",  # Assuming you'll create gemini_api.py
        "class_name": "GeminiAPI",  # Assuming class name will be GeminiAPI
    },
    "llama3": {
        "config_name": "Llama3ConfigClass",
        "module_name": "llama3_api",  # Assuming you'll create llama3_api.py
        "class_name": "Llama3API",  # Assuming class name will be Llama3API
    },
}


@dataclasses.dataclass
class GPT4ConfigClass:
    model: str = "gpt-4"
    api_base: str = os.getenv("OPENAI_BASEURL", "https://api.openai.com/v1")
    # set up the openai key
    openai_key = os.getenv("OPENAI_API_KEY", None)
    if openai_key is None:
        print(
            "Your OPENAI_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 20
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class GPT35Turbo16kConfigClass:
    model: str = "gpt-3.5-turbo-16k"
    api_base: str = os.getenv("OPENAI_BASEURL", "https://api.openai.com/v1")
    # set up the openai key
    openai_key = os.getenv("OPENAI_API_KEY", None)
    if openai_key is None:
        print(
            "Your OPENAI_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 20
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class GPT4Turbo:
    model: str = "gpt-4-1106-preview"
    api_base: str = os.getenv("OPENAI_BASEURL", "https://api.openai.com/v1")
    # set up the openai key
    openai_key = os.getenv("OPENAI_API_KEY", None)
    if openai_key is None:
        print(
            "Your OPENAI_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 10
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class GPT4O:
    model: str = "gpt-4o-2024-05-13"
    api_base: str = os.getenv("OPENAI_BASEURL", "https://api.openai.com/v1")
    # set up the openai key
    openai_key = os.getenv("OPENAI_API_KEY", None)
    if openai_key is None:
        print(
            "Your OPENAI_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 10
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class GPT4ALLConfigClass:
    model: str = "mistral-7b-openorca.Q4_0.gguf"


@dataclasses.dataclass
class TitanConfigClass:
    model: str = "amazon.titan-tg1-large"

@dataclasses.dataclass
class Llama3ConfigClass:
    model: str = "meta-llama/Meta-Llama-3-8B-Instruct"

@dataclasses.dataclass
class AzureGPT35ConfigClass:
    model: str = "gpt-35-turbo"
    api_type: str = "azure"
    api_base: str = "https://docs-test-001.openai.azure.com/"
    openai_key = os.getenv("OPENAI_API_KEY", None)
    if openai_key is None:
        print(
            "Your OPENAI_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 20
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class Gemini10ConfigClass:  # New dataclass for Gemini 1.0
    model: str = "gemini-1.0-pro"
    # api_base: str = "https://api.gemini.com/v1"  # Replace with actual API base URL
    gemini_key = os.getenv(
        "GOOGLE_API_KEY", None
    )  # Assuming environment variable for API key
    if gemini_key is None:
        print(
            "Your GOOGLE_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 20
    is_debugging: bool = False
    log_dir: str = None


@dataclasses.dataclass
class Gemini15ConfigClass:  # New dataclass for Gemini 1.5
    model: str = "gemini-1.5-pro-latest"
    # api_base: str = "https://api.gemini.com/v1"  # Replace with actual API base URL
    gemini_key = os.getenv(
        "GOOGLE_API_KEY", None
    )  # Assuming environment variable for API key
    if gemini_key is None:
        print(
            "Your GOOGLE_API_KEY is not set. Please set it in the environment variable."
        )
    error_wait_time: float = 20
    is_debugging: bool = False
    log_dir: str = None


def dynamic_import(module_name, log_dir, use_langfuse_logging=False) -> object:
    if module_name in module_mapping:
        module_config_name = module_mapping[module_name]["config_name"]
        module_import_name = module_mapping[module_name]["module_name"]
        class_name = module_mapping[module_name]["class_name"]
        module_config = getattr(sys.modules[__name__], module_config_name)
        module_config.log_dir = log_dir

        # import the module
        LLM_module = importlib.import_module(
            "pentestgpt.utils.APIs." + module_import_name
        )
        LLM_class = getattr(LLM_module, class_name)
        # initialize the class
        LLM_class_initialized = LLM_class(
            module_config, use_langfuse_logging=use_langfuse_logging
        )

        return LLM_class_initialized

    else:
        print(
            "Module not found: "
            + module_name
            + ". Falling back to use the default gpt-3.5-turbo-16k"
        )
        # fall back to gpt-3.5-turbo-16k
        LLM_class_initialized = dynamic_import("gpt-3.5-turbo-16k", log_dir)
        return LLM_class_initialized


if __name__ == "__main__":
    # a quick local test
    # load gpt4
    gpt4 = dynamic_import("gpt4all", "logs")
    gpt4.send_new_message("hi")
