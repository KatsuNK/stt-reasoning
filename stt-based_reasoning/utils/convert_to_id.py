import json

def convert_to_task_id(navi, task_names):
    return {task_names[task]:[task_names[next_task] for next_task in next_tasks] for task, next_tasks in navi.items()}


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

    task_names = dict((v,k) for k,v in task_names.items())
    return task_names

if __name__ == '__main__':
    navi_path = '../json/task_navigator.json'
    with open(navi_path, 'r') as navi_file:
        navi = json.load(navi_file)
    tree_path = '../json/task_tree.json'
    with open(tree_path, 'r') as tree_file:
        tree = json.load(tree_file)
    task_names = extract_task_names(tree)
    print(task_names)
    print(navi)
    task_id = convert_to_task_id(navi, task_names)

    # Save the converted task IDs to a new JSON file
    with open('../json/task_navigator_id.json', 'w') as file:
        json.dump(task_id, file, indent=4)