import json
import re

def extract_task(task_dict, task_id):
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
        print(f"Key '{tmp_task_id}' doesn't exist. Try again.")


# Function to update the status of a task
def update_task_status(task_dict, task_id, new_status):
    if new_status not in ['to-do', 'in-progress', 'completed', 'failed']: # if status is wrong
        print(f"Status '{new_status}' doesn't exist. Try again.")
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

        print(f'--------------------------------')
        print(f'Update task {task_id} {current_task['name']}: ({old_status}) -> ({new_status})')
        print(f'--------------------------------')
    except KeyError:
        print(f"Key '{tmp_task_id}' doesn't exist. Try again.")

    # Function to update a finding of a task
def update_task_finding(task_dict, task_id, finding_id, finding):
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

        print(f'--------------------------------')
        print(f'Update finding {finding_id} in task {task_id} {current_task['name']}: {finding}')
        print(f'--------------------------------')
    except KeyError:
        print(f"Key '{tmp_task_id}' doesn't exist. Try again.")


# Function to extract (sub)tasks labeled as 'in-progress'
def working_task_ids(task_dict):
    for key, value in task_dict.items():
        if value.get('status', 0) == 'in-progress':
            yield key

        # Call function recursively
        if isinstance(value['subtasks'], dict):
            yield from working_task_ids(value['subtasks'])
        else:
            yield key


# Function to format the current task list as a string
def format_tasks(task_dict, level=0):
    output = ""
    tab = "\t"
    indent = tab * level  # Indentation based on task depth
    for task_id, task_info in task_dict.items():
        # Ensure task_info is a dictionary and not a string
        if isinstance(task_info, dict):
            output += f"{indent}{task_id}: {task_info['name']} - ({task_info['status']})\n"
            if task_info['findings']:
                for f_id, finding in task_info['findings'].items():
                    output += f"{indent+tab}- <finding {f_id}: {finding}>\n"
            # Recursively format subtasks if they exist
            if "subtasks" in task_info and isinstance(task_info["subtasks"], dict):
                    output += format_tasks(task_info["subtasks"], level + 1)
    return output


    # main function
def update_attack_tree(tasks, descriptions):
    print('----------------------------------------------------------------------------------------------')
    print("<<Update Started>>")

    while True:
        input_type = input("'status' or 'finding'? : ")
        if input_type == 'status': # update completion status
            print('<<Update completion status>>  Format: <task_id>,<status>: [to-do,in-progress,completed,failed]>')
            while True:
                user_input = input("Input here: ")
                if user_input == 'quit' or user_input == '': # when quitting
                    break
                elif user_input.count(',') == 0: # if wrong format
                    print('Different format. Try again.')
                    continue
                else:
                    task_id, new_status = user_input.split(',')
                    update_task_status(tasks, task_id, new_status)


        elif input_type == 'finding': # update finding
            print('<<Update finding>>  Format: <task_id>,<finding id>,<finding>')
            while True:
                user_input = input("Input here: ")
                if user_input == 'quit' or user_input == '': # when quitting
                    break
                elif user_input.count(',') == 0: # if wrong format
                    print('Different format. Try again.')
                    continue
                else:
                    matches = list(re.finditer(',', user_input)) # use re to ignore commas after the first two commas
                    m1_st, m1_end, m2_st, m2_end = matches[0].start(), matches[0].end(), matches[1].start(), matches[1].end()
                    task_id, finding_id, finding = user_input[:m1_st].strip(), user_input[m1_end:m2_st].strip(), user_input[m2_end:].strip()
                    update_task_finding(tasks, task_id, finding_id, finding)

        elif input_type == 'quit' or input_type == '': # when quitting
            break
        else: # typo
            print("Please type 'status' or 'finding'. Type 'quit' or nothing to quit updating status and finding")

    AT = "The Entire Attack Tree:\n" + format_tasks(tasks)

    # add in-progress task descriptions
    working_ids = [working_id for working_id in working_task_ids(tasks)]

    highest_level = working_ids[working_ids.index(max(working_ids))]
    extracted = {highest_level: extract_task(tasks, highest_level)}
    partial_AT = format_tasks(extracted)
    partial_AT = "Partial Attack Tree:\n" + partial_AT

    lowest_level = working_ids[working_ids.index(max(working_ids))]
    extracted = {lowest_level: extract_task(tasks, lowest_level)}
    current_task = format_tasks(extracted)
    current_task = "Current Task in Progress:\n" + partial_AT

    # add task description
    task_names = extract_task_names(tasks)
    for working_id in working_ids:
        task_name = task_names[working_id]
        working_description = descriptions.get(task_name, "")
        if working_description:
            name_description = task_name + " (in-progress):\n" + working_description
        else:
            name_description = ""
        AT += "\n" + name_description
        partial_AT += "\n" + name_description
        current_task += "\n" + name_description

    return AT, partial_AT, current_task

def extract_task_names(task_dict):
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

if __name__ == '__main__':
    # Load the tasks from a JSON file
    with open('json/init_tasks_v1.json', 'r') as file:
            tasks = json.load(file)

    with open('json/task_descriptions.json', 'r') as file:
            task_descriptions = json.load(file)

    at, partial_at, current_task = update_attack_tree(tasks, task_descriptions)
    print(at)
