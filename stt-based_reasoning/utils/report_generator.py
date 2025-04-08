# a quick report generation script that converts the saved logs file into a pdf.
import datetime
import json
import os
import sys
import time


def main(file_name, model_id):
    model_names = ["llama-3", "gemini-1.5", "gpt-4"]
    model_name = model_names[model_id]

    # load the file into json
    with open(file_name, "r") as f:
        logs = json.load(f)
    user_inputs = logs["user"]
    bot_responses = logs[model_name]
    merged_list = [[user_input[0], user_input[1], "user"] for user_input in user_inputs]
    merged_list.extend(
        [bot_response[0], bot_response[1], model_name]
        for bot_response in bot_responses
    )
    merged_list.sort(key=lambda x: x[0])

    # now print the conversation
    output = ""
    for element in merged_list:
        # convert the timestamp to a human readable format
        timestamp = datetime.datetime.fromtimestamp(int(element[0])).strftime(
            "%H:%M:%S"
        )
        output += f"{timestamp} [{element[2]}]: {element[1]}\n"
        # add an additional line break if the element is from bot
        if element[2] == model_name:
            output += "----------------------------------------\n\n"
    # print the output
    print("Conversation log: ")

    print(output)


if __name__ == "__main__":
    # default filename = "../logs/sample_log.txt"
    if len(sys.argv) == 1:
        file_name = "logs/sample_log.txt"
    else:
        file_name = sys.argv[1]
        model_id = sys.argv[2]
    main(file_name, model_id)
