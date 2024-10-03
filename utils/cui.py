import io
import json
import os
import uuid
import urllib.request
import urllib.parse
import websocket
from PIL import Image
from job.models.Job import Job

SERVER_ADDRESS = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


def read_json_from_file(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")

    with open(file_path, "r", encoding="utf-8") as file:
        json_string = file.read()
        return json.loads(json_string)


def queue_prompt(prompt, client_id):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request(f"http://{SERVER_ADDRESS}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(
        f"http://{SERVER_ADDRESS}/view?{url_values}"
    ) as response:
        return response.read()


def get_history(prompt_id):
    with urllib.request.urlopen(
        f"http://{SERVER_ADDRESS}/history/{prompt_id}"
    ) as response:
        return json.loads(response.read())


def get_images(ws, prompt, client_id, job_id):
    prompt_id = queue_prompt(prompt, client_id)["prompt_id"]
    output_images = {}

    # Fetch the job instance once at the start
    job = Job.objects.get(id=job_id)
    print('starting the loop')

    while True:
        try:
            out = ws.recv()
            if isinstance(out, str):
                # Log the message to the console and append to the job logs
                print(f"WebSocket message: {out}")
                message = json.loads(out)

                # Append log to the job's logs field and save incrementally
                job.logs = (job.logs or "") + out + "\n"
                job.save()  # Save the logs incrementally to the database

                if message["type"] == "executing":
                    data = message["data"]
                    if data["node"] is None and data["prompt_id"] == prompt_id:
                        break  # Execution is done
            else:
                print(f"Non-string message received: {out}")
        except websocket.WebSocketException as e:
            job.logs = (job.logs or "") + f"WebSocket Error: {str(e)}\n"
            job.save()
            print(f"WebSocket Error: {str(e)}\n")
            break  # Exit the loop on WebSocket error

    # Fetch the job's history after WebSocket execution
    history = get_history(prompt_id)[prompt_id]
    print(history)

    # Process output images
    for node_id in history["outputs"]:
        node_output = history["outputs"][node_id]
        images_output = []
        if "images" in node_output:
            for image in node_output["images"]:
                image_data = get_image(
                    image["filename"], image["subfolder"], image["type"]
                )
                images_output.append(image_data)
        output_images[node_id] = images_output

    return output_images


def run_workflow(prompt, job_id, client_id):
    # Start WebSocket connection
    ws = websocket.WebSocket()
    ws.connect(f"ws://{SERVER_ADDRESS}/ws?clientId={client_id}")
    print("WebSocket connected...")

    try:
        # Run the image generation process and pass the job ID for logging
        print(job_id)
        images = get_images(ws, prompt, client_id, job_id)
        job = Job.objects.get(id=job_id)

        # Update job output images in the database
        # job.result_data = images
        job.status = "completed"
        print('completed')
    except Exception as e:
        job = Job.objects.get(id=job_id)
        # Log errors in the job logs field
        job.status = "failed"
        job.logs = (job.logs or "") + f"Error: {str(e)}\n"
        print(f"Error: {str(e)}\n")
        # job.output_images = {"error": str(e)}
    finally:
        job.save()
        ws.close()

    # Display images (optional)
    for node_id in images:
        for image_data in images[node_id]:
            image = Image.open(io.BytesIO(image_data))
            image.show()

    return images


import json


def replace_user_inputs(workflow_data, workflow_inputs, user_inputs):
    """
    Replaces inputs in the workflow with the user-provided data.
    workflow_data: The original workflow JSON (already deserialized as a Python dict).
    workflow_inputs: The mapping of inputs in the workflow {node_id: input_name}.
    user_inputs: The user-provided inputs for the job {node_id: {input_name: input_value}}.
    """
    # Loop through each node and its input in the workflow's input mapping
    for node_id, input_name in workflow_inputs.items():
        if node_id in workflow_data and "inputs" in workflow_data[node_id]:
            # If the user has provided inputs for this node
            if node_id in user_inputs:
                # Loop through the user-provided input values and assign them
                for input_name, input_value in user_inputs[node_id].items():
                    # Replace the corresponding input in the workflow
                    if input_name in workflow_data[node_id]["inputs"]:
                        workflow_data[node_id]["inputs"][input_name] = input_value

    return workflow_data
