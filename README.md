# Guided Reasoning in LLM-Driven Penetration Testing Using Structured Attack Trees

This repository implements the guided reasoning pipeline proposed in our COLM 2025 paper:
**"Guided Reasoning in LLM-Driven Penetration Testing Using Structured Attack Trees."**

## Overview

Traditional LLM-based agents for penetration testing rely heavily on self-guided reasoning, often resulting in hallucinated or inefficient actions. To address this, we propose a **Structured Task Tree (STT)** approach grounded in the **MITRE ATT&CK Matrix**, enabling LLMs to follow a deterministic attack progression rather than generating tasks autonomously.

This repository contains two implementations:
- `pentestgpt/`: A reproduction of the self-guided baseline system as in Deng et al. (2024)
- `stt-based_reasoning/`: Our proposed guided reasoning pipeline using structured attack trees

---

## Installation (Python 3.12.4)

Install dependencies for both baseline and proposed methods:

```bash
cd pentestgpt && pip install -r requirements.txt
cd ../stt-based_reasoning && pip install -r requirements.txt
```

---

## API Setup

To use cloud-based models (Gemini and GPT), you'll need API keys:

### Llama (Local via HuggingFace Transformers)

1. Create an account at [Hugging Face](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct)
2. Generate an access token
3. Insert the token in `llama3_api.py` at [line 56](./stt-based_reasoning/utils/APIs/llama3_api.py)

### Gemini

```bash
export GOOGLE_API_KEY=<YOUR_API_KEY>
source ~/.bashrc
```

Key available at [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key)

### GPT (OpenAI)

```bash
export OPENAI_API_KEY=<YOUR_API_KEY>
source ~/.bashrc
```

Key available from [OpenAI Platform](https://platform.openai.com/api-keys)

---

## Usage

### 1. Run Self-Guided Reasoning (PentestGPT Baseline)

```bash
cd pentestgpt
python main.py --reasoning_model gemini-1.5 --parsing_model gemini-1.5
```

- Available models: `llama-3`, `gemini-1.5`, `gpt-4`

### 2. Run STT-Based Reasoning (Our Method)

```bash
cd stt-based_reasoning
python main.py --model_id 1
```

- `model_id` options:
  - `0` → Llama3-8B (local)
  - `1` → Gemini-1.5 (API)
  - `2` → GPT-4 (API)

## How to run the tools on HackTheBox machines

### Install [Kali-linux](https://www.kali.org/docs/installation/hard-disk-install/)

- For Windows, [Kali WSL](https://www.kali.org/docs/wsl/wsl-preparations/) is also available

### Spawn a HTB machine

1. Go to [HackTheBox website](https://app.hackthebox.com/machines)
2. Select and spawn a machine to obtain its IP address
3. Download <YOUR_HTB_USERNAME>.opvn from the "CONNECT TO HTB" tab

### Check OpenVPN connection

```bash
sudo openvpn <PATH_TO_YOUR_OPVN>
ping <MACHINE_IP_ADDRESS>
```

### How to start

- Both our method and PentestGPT start a session with:

```
Please describe the penetration testing task in one line, including the target IP, task type, etc.
> 
```

- Example
  
```
> I want to pentest <MACHINE_IP_ADDRESS>, which is a machine from HackTheBox
```
