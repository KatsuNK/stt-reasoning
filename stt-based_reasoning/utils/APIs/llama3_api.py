import dataclasses
import json
import os
from typing import Any, Dict, List, Tuple

import boto3
import loguru
import tiktoken
from tenacity import *

import transformers
import torch

from pentestgpt.utils.llm_api import LLMAPI

logger = loguru.logger
logger.remove()


@dataclasses.dataclass
class Message:
    ask_id: str = None
    ask: dict = None
    answer: dict = None
    answer_id: str = None
    request_start_timestamp: float = None
    request_end_timestamp: float = None
    time_escaped: float = None


@dataclasses.dataclass
class Conversation:
    conversation_id: str = None
    message_list: List[Message] = dataclasses.field(default_factory=list)

    def __hash__(self):
        return hash(self.conversation_id)

    def __eq__(self, other):
        if not isinstance(other, Conversation):
            return False
        return self.conversation_id == other.conversation_id



class Llama3API(LLMAPI):

    # llama3 setup
    pipeline = transformers.pipeline(
        "text-generation",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        model_kwargs={
            "torch_dtype": torch.bfloat16
            },
        device_map="auto",
        token = '' # token from Hugging Face required
    )
    terminators = [
        pipeline.tokenizer.eos_token_id,
        pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>"),
    ]

    num_queries = 0

    def __init__(self, config_class, use_langfuse_logging=False):
        self.name = str(config_class.model)
        self.model = config_class.model
        self.log_dir = config_class.log_dir
        self.history_length = 2  # maintain 2 messages in the history. (2 chat memory)
        self.conversation_dict: Dict[str, Conversation] = {}
        self.error_waiting_time = 3  # wait for 3 seconds
        logger.add(sink=os.path.join(self.log_dir, "llama3.log"), level="WARNING")

    def _chat_completion(
        self, history: List, model="meta-llama/Meta-Llama-3-8B-Instruct", temperature=0.6
    ) -> str:
        """
        :param history: a list of strings
        :return: a string
        """
        try:
            #print("history: ", history)
            #print("modelId: ", modelId)
            prompt = Llama3API.pipeline.tokenizer.apply_chat_template(
                history, tokenize=False, add_generation_prompt=True
            )
            outputs = Llama3API.pipeline(
                prompt,
                max_new_tokens=4096,
                eos_token_id=Llama3API.terminators,
                do_sample=True,
                temperature=temperature,
                top_p=0.9,
            )

            # evaluation
            Llama3API.num_queries += 1

            response = outputs[0]["generated_text"][len(prompt):]

            return response

        except Exception as e:
           logger.error(f"Error: {e}")
           return None


if __name__ == "__main__":
    from module_import import Llama3ConfigClass

    config_class = Llama3ConfigClass()
    config_class.log_dir = "logs"
    llama3 = Llama3API(config_class)

    # test is below
    # 1. create a new conversation
    result, conversation_id = llama3.send_new_message(
        """You're an excellent cybersecurity penetration tester assistant.
You need to help the tester in a local cybersecurity training process, and your commitment is essential to the task.
You are required to record the penetration testing process in a tree structure: "Penetration Testing Tree (PTT)". It is structured as follows:
(1) The tasks are in layered structure, i.e., 1, 1.1, 1.1.1, etc. Each task is one operation in penetration testing; task 1.1 should be a sub-task of task 1.
(2) Each task has a completion status: to-do, completed, or not applicable.
(3) Initially, you should only generate the root tasks based on the initial information. In most cases, it should be reconnaissance tasks. You don't generate tasks for unknown ports/services. You can expand the PTT later.

You shall not provide any comments/information but the PTT. You will be provided with task info and start the testing soon. Reply Yes if you understand the task."""
    )
    print("Answer 1")
    print(result)
