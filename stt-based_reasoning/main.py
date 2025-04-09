import os
import sys
import time
import json
import re
import traceback

import argparse
import loguru
from rich.console import Console
import transformers
import torch

from task_update import update_attack_tree

from prompts import Prompt
from prompt_toolkit.formatted_text import HTML
from utils.APIs.module_import import dynamic_import
from utils.prompt_select import prompt_ask, prompt_select
from utils.task_handler import (
    task_entry,
    local_task_entry,
    TaskCompleter,
    LocalTaskCompleter,
)

logger = loguru.logger


class PentestSTT():
    def __init__(self, json_path='json/task_tree.json', task_nav_path='json/task_navigator_id.json', log_dir='logs', model_id=0):
        # log
        self.log_dir = log_dir
        logger.add(sink=os.path.join(log_dir, "Pentest.log"))
        self.save_dir = "test_history"
        model_configs = ["llama-3", "gemini-1.5", "gpt-4"]
        self.model_name = model_configs[model_id]
        self.history = { # history for log
            "user": [],
            self.model_name: [],
            "exception": []
        }

        self.prompts = Prompt()
        self.conversation = None # session id for Gemini
        self.local_conversation = [] # local conversation history for Gemini
        self.history_length = 2 # length of the history input to Gemini
        self.indent = ' '*4

        self.console = Console()
        # print the initialization message on the current implementation.
        self.console.print("Settings: ")
        self.console.print(f" - model: {self.model_name}", style="bold green")
        self.console.print(f" - log directory: {log_dir}", style="bold green")

        # load Predefined Attack Tree (PAT) and description
        self.json_path = json_path
        with open(self.json_path, 'r') as file:
            self.task_dict = json.load(file)
        with open(task_nav_path, 'r') as file:
            self.task_navigator = json.load(file)
        self.task_names = self.extract_task_names(self.task_dict) # mapping task id to task name to get task descriptions

        # manage recent and old finished task ids
        self.completed_task_id_list = []
        self.recent_completed_task_id = None

        # model settings
        with self.console.status(f"[bold green] Loading {self.model_name}...") as status:
            self.model = dynamic_import(
                self.model_name, self.log_dir, use_langfuse_logging=False
            )


    def log_conversation(self, source, text):
        """
        append the conversation into the history

        Parameters:
        ----------
        source: str
            the source of the conversation
        text: str
            the content of the conversation
        """
        # append the conversation into the history
        timestamp = time.time()
        if source not in self.history.keys():
            # an exception
            source = "exception"
        self.history[source].append((timestamp, text))


    def get_response(self, query, message_history=[], max_tokens=4096, temperature=0.6, top_p=0.9, local=False):
        if not local:
            message_history = message_history if len(message_history) <= self.history_length else message_history[-self.history_length:]
        user_prompt = message_history + [{"role": "user", "content": query}]
        prompt = self.pipeline.tokenizer.apply_chat_template(
            user_prompt, tokenize=False, add_generation_prompt=True
        )
        outputs = self.pipeline(
            prompt,
            max_new_tokens=max_tokens,
            eos_token_id=self.terminators,
            do_sample=True,
            temperature=temperature,
            top_p=top_p,
        )

        response = outputs[0]["generated_text"][len(prompt):]
        return response, user_prompt + [{"role": "system", "content": response}]


    def extract_task_names(self, task_dict):
        task_names = {}

        # Recursive function to traverse the nested dictionary
        def traverse(tasks):
            for task_id, task_info in tasks.items():
                if 'name' in task_info:
                    task_names[task_id] = task_info['name']
                if 'subtasks' in task_info and isinstance(task_info['subtasks'], dict):
                    traverse(task_info['subtasks'])

        traverse(task_dict)
        return task_names


    def extract_task(self, task_dict, task_id):
        tmp_task_id = task_id
        keys = task_id.replace(" ", "").split(".")  # break down the task_id to navigate through subtasks
        current_task = task_dict
        keys_list = [".".join(keys[:i]) for i in range(1, len(keys) + 1)] # generate path to the deepest (sub)task
        try:
            # for subtasks
            for i, key in enumerate(keys_list):
                if i == 0:
                    current_task = current_task[key]  # only for the first level
                else:
                    current_task = current_task['subtasks'][key]  # navigate to subtasks
            return current_task
        except KeyError:
            self.console.print(f"Key '{tmp_task_id}' doesn't exist. Try again.", style="bold red")


    def update_task_status(self, task_dict, task_id, new_status):
        if new_status not in ['to-do', 'in-progress', 'completed', 'failed']: # if status is wrong
            self.console.print(f"Status '{new_status}' doesn't exist. Try again.", style="bold red")
            return 0

        tmp_task_id = task_id
        keys = task_id.replace(" ", "").split(".")  # break down the task_id to navigate through subtasks
        current_task = task_dict
        keys_list = [".".join(keys[:i]) for i in range(1, len(keys) + 1)] # generate path to the deepest (sub)task

        try:
            # for subtasks
            for i, key in enumerate(keys_list):
                if i == 0:
                    current_task = current_task[key]  # only for the first level
                else:
                    current_task = current_task['subtasks'][key]  # navigate to subtasks

            old_status = current_task["status"]
            current_task["status"] = new_status  # update the status

            result = f"""
            --------------------------------
            Update task {task_id} {current_task['name']}: ({old_status}) -> ({new_status})
            --------------------------------
            """
            self.console.print(result)
            return result
        except KeyError:
            self.console.print(f"Key '{tmp_task_id}' doesn't exist. Try again.", style="bold red")


    def update_task_finding(self, task_dict, task_id, finding_id, finding):
        tmp_task_id = task_id
        keys = task_id.replace(" ", "").split(".")  # Break down the task_id to navigate through subtasks
        current_task = task_dict
        keys_list = [".".join(keys[:i]) for i in range(1, len(keys) + 1)] # generate path to the deepest (sub)task

        try:
            # for subtasks
            for i, key in enumerate(keys_list):
                if i == 0:
                    current_task = current_task[key]  # Only for the first level
                else:
                    current_task = current_task['subtasks'][key]  # Navigate to subtasks

            current_task["findings"][str(finding_id)] = finding  # Update the status
            result = f"""
            --------------------------------
            Update finding {finding_id} in task {task_id} {current_task['name']}: {finding}
            --------------------------------
            """
            self.console.print(result)
            return result

        except KeyError:
            self.console.print(f"Key '{tmp_task_id}' doesn't exist. Try again.", style="bold red")


    def working_task_ids(self, task_dict):
        for key, value in task_dict.items():
            if value.get('status', 0) == 'in-progress':
                yield key

            # Call function recursively
            if isinstance(value['subtasks'], dict):
                yield from self.working_task_ids(value['subtasks'])
            else:
                yield key


    def finished_task_ids(self, task_dict):
        for key, value in task_dict.items():
            if value.get('status', 0) == ('completed' or 'failed'):
                yield key

            # Call function recursively
            if isinstance(value['subtasks'], dict):
                yield from finished_task_ids(value['subtasks'])
            else:
                yield key


    def format_tasks(self, task_dict, level=0):
        output = ""
        ind = self.indent * level  # Indentation based on task depth
        for task_id, task_info in task_dict.items():
            # Ensure task_info is a dictionary and not a string
            if isinstance(task_info, dict):
                output += f"{ind}{task_id}: {task_info['name']} - ({task_info['status']})\n"
                if task_info['findings']:
                    for f_id, finding in task_info['findings'].items():
                        output += f"{ind+self.indent}- <finding {f_id}: {finding}>\n"
                # Recursively format subtasks if they exist
                if "subtasks" in task_info and isinstance(task_info["subtasks"], dict):
                        output += self.format_tasks(task_info["subtasks"], level + 1)
        return output


    def update_task_tree(self):
        self.console.rule("[bold red]Updated Started")

        updated_result = "\n--------------------- Update Started ---------------------\n" # for logging
        response = True
        while True:
            request_option = task_entry()
            if request_option == 'status': # update completion status
                updated_result += 'Update Status:\n'
                while True:
                    user_input = prompt_ask("Update completion status (format: <task_id>,<status: to-do/in-progress/completed/failed>)\n>", multiline=False)
                    if user_input == 'quit' or user_input == '': # when quitting
                        break
                    elif user_input.count(',') == 1:
                        task_id, new_status = user_input.split(',')
                        # append recent finished task
                        if new_status == 'completed':
                            self.recent_completed_task_id = task_id
                            self.completed_task_id_list.append(task_id)

                            if not self.task_navigator[task_id]: # if navigator is empty
                                self.recent_completed_task_id = self.completed_task_id_list[-1] # take one step back

                        if new_status == 'failed':
                            self.recent_completed_task_id = self.completed_task_id_list[-1] # take one step back
                        status_result = self.update_task_status(self.task_dict, task_id, new_status)
                        updated_result += status_result
                    else: # if wrong format
                        self.console.print('Different format. Try again.', style='bold red')
                        continue


            elif request_option == 'findings': # update finding
                updated_result += 'Update Findings:\n'
                while True:
                    user_input = prompt_ask("<<Update finding>>  Format: <task_id>,<finding id>,<finding>\n>", multiline=False)
                    if user_input == 'quit' or user_input == '': # when quitting
                        break
                    elif user_input.count(',') >= 2:
                        matches = list(re.finditer(',', user_input)) # use re to ignore commas after the first two commas
                        m1_st, m1_end, m2_st, m2_end = matches[0].start(), matches[0].end(), matches[1].start(), matches[1].end()
                        task_id, finding_id, finding = user_input[:m1_st].strip(), user_input[m1_end:m2_st].strip(), user_input[m2_end:].strip()
                        findings_result = self.update_task_finding(self.task_dict, task_id, finding_id, finding)
                        updated_result += findings_result
                    else: # if wrong format
                        self.console.print('Different format. Try again.', style='bold red')
                        continue

            elif request_option == "tree":
                entire_AT = "\nThe Entire Predefined Attack Tree:\n" + self.format_tasks(self.task_dict)
                updated_result += entire_AT
                self.console.print(entire_AT)

            elif request_option == "next":
                self.console.print("Proceed to the next step.", style="bold green")
                updated_result += "\n--------------------- Update Finished ---------------------\n"
                self.log_conversation("user", updated_result)
                break

            elif request_option == "quit":
                response = False
                self.console.print("End this session.", style="bold green")
                updated_result += "\n--------------------- Update Finished ---------------------\n"
                self.log_conversation("user", updated_result)
                break
            else:
                self.console.print("Please key in the correct options.", style="bold red")
                self.log_conversation("user", "Please key in the correct options.")

        # extract current task
        working_ids = [working_id for working_id in self.working_task_ids(self.task_dict)]
        if working_ids:
            lowest_level = working_ids[working_ids.index(max(working_ids))]
            extracted = {lowest_level: self.extract_task(self.task_dict, lowest_level)}
            current_task = self.format_tasks(extracted)
            current_task = "Current Task in Progress:\n" + current_task + "\n" + "Description of Current Task: " + extracted[lowest_level]['description']
        else:
            current_task = "Current Task in Progress: None"

        return current_task, response


    def feed_init_prompt(self):
        # Provide basic information of the task
        init_description = prompt_ask(
            "Please describe the penetration testing task in one line, including the target IP, task type, etc.\n> ",
            multiline=False,
        )

        current_task, response = self.update_task_tree()
        prefixed_init = self.prompts.init + init_description + "\n" + current_task
        self.log_conversation("user", prefixed_init)

        with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
            init_response, self.conversation = self.model.send_new_message(prefixed_init)
            self.console.print(f"{self.model_name} output: ", style="bold green")
            self.console.print(init_response)
            self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + init_response)

        return current_task, response


    def local_task(self):
        self.console.rule("[bold red]Local task discussion")
        self.local_conversation = []
        first_time = 1
        updated_result = ""
        while True:
            request_option = local_task_entry()
            if request_option == 'more': # local task loop
                user_input = prompt_ask(f"Please share your thoughts/questions with the {self.model_name} response. (End with <shift + right-arrow>)\n>", multiline=True)
                if first_time:
                    updated_result = "\n--------------------- Update Started ---------------------\n" # for logging
                    local_task_prompt = self.prompts.local_task_init + user_input
                    self.log_conversation("user", f"User: {local_task_prompt}")
                    with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
                        local_response, self.local_conversation = self.model.send_new_message(local_task_prompt)
                        self.console.print(f"{self.model_name} output: ", style="bold green")
                        self.console.print(local_response)
                        self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + local_response)
                else:
                    first_time = 0
                    local_task_prompt = self.prompts.local_task + user_input
                self.log_conversation("user", f"User: {local_task_prompt}")
                with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
                    local_response = self.model.send_message(local_task_prompt, self.local_conversation)
                    self.console.print(f"{self.model_name} output: ", style="bold green")
                    self.console.print(local_response)
                    self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + local_response)
            if request_option == 'status': # update completion status
                updated_result += 'Update Status:\n'
                while True:
                    user_input = prompt_ask("Update completion status (format: <task_id>,<status: to-do/in-progress/completed/failed>)\n>", multiline=False)
                    if user_input == 'quit' or user_input == '': # when quitting
                        break
                    elif user_input.count(',') == 1:
                        task_id, new_status = user_input.split(',')
                        status_result = self.update_task_status(self.task_dict, task_id, new_status)
                        updated_result += status_result
                    else: # if wrong format
                        self.console.print('Different format. Try again.', style='bold red')
                        continue
            elif request_option == 'findings': # update finding
                updated_result += 'Update Findings:\n'
                while True:
                    user_input = prompt_ask("<<Update finding>>  Format: <task_id>,<finding id>,<finding>\n>", multiline=False)
                    if user_input == 'quit' or user_input == '': # when quitting
                        break
                    elif user_input.count(',') >= 2:
                        matches = list(re.finditer(',', user_input)) # use re to ignore commas after the first two commas
                        m1_st, m1_end, m2_st, m2_end = matches[0].start(), matches[0].end(), matches[1].start(), matches[1].end()
                        task_id, finding_id, finding = user_input[:m1_st].strip(), user_input[m1_end:m2_st].strip(), user_input[m2_end:].strip()
                        findings_result = self.update_task_finding(self.task_dict, task_id, finding_id, finding)
                        updated_result += findings_result
                    else: # if wrong format
                        self.console.print('Different format. Try again.', style='bold red')
                        continue
            elif request_option == "tree":
                entire_AT = "\nThe Entire Predefined Attack Tree:\n" + self.format_tasks(self.task_dict)
                updated_result += entire_AT
                self.console.print(entire_AT)
            elif request_option == 'continue': # exit local task
                if not first_time:
                    self.console.print("End local task discussion.", style="bold green")
                    updated_result += "\n--------------------- Update Finished ---------------------\n"
                    self.log_conversation("user", updated_result)
                break


    def select_next_task(self):
        if self.recent_completed_task_id is not None:
            task_candidates = self.task_navigator[self.recent_completed_task_id]

            completed_task = self.format_tasks({self.recent_completed_task_id: self.extract_task(self.task_dict, self.recent_completed_task_id)}) # str
            candidates_txt = f"Completed task status and findings:\n {completed_task}\n\n"
            for i, cand_id in enumerate(task_candidates):
                task_cand = self.extract_task(self.task_dict, cand_id)
                print(task_cand['name'], task_cand['status'])
                if task_cand['status'] != ('completed' or 'failed'): # exclude failed and completed task
                    cand_txt = f"Candidate task {cand_id} {task_cand['name']}: {task_cand['description']}\n\n"
                    candidates_txt += cand_txt

            self.console.print("Possible Next Tasks: ", style="bold green")
            self.console.print(candidates_txt)

            task_selection_prompt = self.prompts.task_selection + candidates_txt
            self.log_conversation("user", f"User: {task_selection_prompt}")

            # load partial task tree and ask what are the key findings and what to update
            self.console.rule(f"[bold red]{self.model_name} Task Selection")
            with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
                task_selection_response = self.model.send_message(task_selection_prompt, self.conversation)
                self.console.print(f"{self.model_name} output: ", style="bold green")
                self.console.print(task_selection_response)
                self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + task_selection_response)

            self.recent_completed_task_id = None # reset


    def main(self):
        # initialize
        current_task, response = self.feed_init_prompt()

        # enter the main loop.
        while response:
            try:
                self.console.print("Your input: (End with <shift + right-arrow>)", style="bold green")
                user_input = prompt_ask("> ", multiline=True)

                # enter local task
                self.local_task()

                analysis_prompt = self.prompts.output_summarization + "Tester:\n" + user_input + "\n" + current_task

                self.log_conversation("user", f"User: {analysis_prompt}")

                # load partial task tree and ask what are the key findings and what to update
                self.console.rule(f"[bold red]{self.model_name} Suggestion")
                with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
                    analysis_response = self.model.send_message(analysis_prompt, self.conversation)
                    self.console.print(f"{self.model_name} output: ", style="bold green")
                    self.console.print(analysis_response)
                    self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + analysis_response)

                # update task status and add findings to current task
                current_task, response = self.update_task_tree()
                if response == False:
                    break

                # select next task
                self.select_next_task()

                # update task status and add findings to current task
                current_task, response = self.update_task_tree()
                if response == False:
                    break

                generation_prompt = self.prompts.command_generation + "Your analysis:\n" + analysis_response + '\n' + current_task
                self.log_conversation("user", f"User: {generation_prompt}")

                # load currnet task and ask executable commnads for the task
                self.console.rule(f"[bold red]{self.model_name} Command Generation")
                with self.console.status(f"[bold green] {self.model_name} Thinking...") as status:
                    generation_response = self.model.send_message(generation_prompt, self.conversation)
                    self.console.print(f"{self.model_name} output: ", style="bold green")
                    self.console.print(generation_response)
                    self.log_conversation(f"{self.model_name}", f"{self.model_name} output:" + generation_response)


            except Exception as e:  # catch all general exception.
                # log the exception
                self.log_conversation("exception", str(e))
                # print the exception
                self.console.print(f"Exception: {str(e)}", style="bold red")
                # add a more detailed debugging
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                self.console.print("Exception details are below. You may submit an issue on github and paste the error trace", style="bold green")
                # self.console.print(exc_type, fname, exc_tb.tb_lineno)
                print(traceback.format_exc())
                # safely quit the session
                break

        # log the session. Save self.history into a txt file based on timestamp
        timestamp = time.time()
        log_name = f"log_{self.model_name}_{time.strftime('%H-%M-%S', time.localtime(timestamp))}_nq{self.model.num_queries}.txt"
        # save it in the logs folder
        log_path = os.path.join(self.log_dir, log_name)
        with open(log_path, "w") as f:
            json.dump(self.history, f)

        # save the task tree state
        with open(self.json_path[:-5]+str(timestamp)+'.json', 'w') as file:
            json.dump(self.task_dict, file, indent=self.indent)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    #parser.add_argument("json_path", type=str, default='json/task_tree.json', help="path to task tree (.json)")
    #parser.add_argument("task_nav_path", type=str, default='json/task_navigator_id.json', help="path to navigator (.json)")
    #parser.add_argument("log_dir", type=str, default='logs', help="path to logging directory")
    parser.add_argument("--model_id", type=int, default=0, help="model id: 0 (Llama), 1 (Gemini), 2 (GPT)")
    #argv = ["", "generic_json/generic_task_tree.json", "generic_json/task_navigator_id.json", "logs", "1"]
    args = parser.parse_args()
    pentest = PentestSTT(model_id=args.model_id)
    pentest.main()
