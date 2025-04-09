# Guided Reasoning in LLM-Driven Penetration Testing Using Structured Attack Trees

## Installation (Python 3.12.4)

```
cd pentestgpt && pip install -r requirements.txt
cd stt-based_reasoning && pip install -r requirements.txt
```

## API Setup

### Llama (Using Hugging Face's Transformers Library)

- Create a [Hugging Face](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) account and generate an access token

- Put the access toekn in [llama3_api.py](./stt-based_reasoning/utils/APIs/llama3_api.py) (line 56)

### Gemini

- Get a Gemini API Key from [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key)

```
export GOOGLE_API_KEY=<YOUR_API_KEY_HERE>
source ~/.bashrc
```

### GPT

- Get a GPT API Key from [OpenAI Platform](https://platform.openai.com/api-keys)

```
export OPENAI_API_KEY=<YOUR_API_KEY_HERE>
source ~/.bashrc
```

## Command Example to Run Self-guided Reasoning (PentestGPT)

```
cd pentestgpt
python main.py --reasoning_model gemini-1.5 --parsing_model gemini-1.5
```

## Command Example to Run STT-based Reasoning

```
cd stt-based_reasoning
python main.py --model_id 1
```

- model_id: 0 (Llama 3), 1 (Gemini 1.5), 2 (GPT 4)