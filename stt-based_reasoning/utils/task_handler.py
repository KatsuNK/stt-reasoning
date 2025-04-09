"""
url: https://github.com/prompt-toolkit/python-prompt-toolkit/tree/master/examples/prompts/auto-completion
Demonstration of a custom completer class and the possibility of styling
completions independently by passing formatted text objects to the "display"
and "display_meta" arguments of "Completion".
"""
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import CompleteStyle, prompt

class TaskCompleter(Completer):
    tasks = [
        "status",
        "findings",
        "tree",
        "next",
        "quit",
    ]

    task_meta = {
        "status": HTML("Update status."),
        "findings": HTML("Add findings."),
        "tree": HTML("Show the entire AT."),
        "next": HTML("Proceed to the next step."),
        "quit": HTML("End the current session."),
    }

    task_details = """
Below are the available tasks:
 - status: Update status in AT.
 - findings: Add findings in AT.
 - tree: Show the entire AT.
 - next: Proceed to the next step.
 - quit: End the current session."""

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        for task in self.tasks:
            if task.startswith(word):
                yield Completion(
                    task,
                    start_position=-len(word),
                    display=task,
                    display_meta=self.task_meta.get(task),
                )

class LocalTaskCompleter(Completer):
    tasks = [
        "web-search"
        "more",
        "status",
        "findings",
        "tree",
        "continue",
    ]

    task_meta = {
        "more": HTML("Discuss more about generated commands."),
        "web-search": HTML("Ask keywords you should look up."),
        "status": HTML("Update status."),
        "findings": HTML("Add findings."),
        "tree": HTML("Show the entire AT."),
        "continue": HTML("Continue to the next step."),
    }

    task_details = """
Below are the available tasks:
 - more: Discuss more about generated commands.
 - web-search: Ask keywords you should look up.
 - status: Update status in AT.
 - findings: Add findings in AT.
 - tree: Show the entire AT.
 - continue: Continue to the next step."""

    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        for task in self.tasks:
            if task.startswith(word):
                yield Completion(
                    task,
                    start_position=-len(word),
                    display=task,
                    display_meta=self.task_meta.get(task),
                )


def task_entry(text="> "):
    """
    Entry point for the task prompt. Auto-complete
    """
    task_completer = TaskCompleter()
    while True:
        result = prompt(text, completer=task_completer)
        if result not in task_completer.tasks:
            print("Invalid task, try again.")
        else:
            return result


def local_task_entry(text="> "):
    """
    Entry point for the task prompt. Auto-complete
    """
    task_completer = LocalTaskCompleter()
    while True:
        result = prompt(text, completer=task_completer)
        if result not in task_completer.tasks:
            print("Invalid task, try again.")
        else:
            return result

if __name__ == "__main__":
    task_entry()
