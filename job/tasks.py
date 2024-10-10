import io
import os
import json
from PIL import Image
from django.conf import settings
from django.utils.timezone import now
from celery import shared_task
from job.models.Job import Job
from job.models.Dataset import Dataset, DatasetImage
from utils.cui import run_workflow  # Assuming run_workflow function is defined in utils

@shared_task(bind=True)
def run_workflow_task(self, job_id, modified_workflow):
    """
    Celery task to execute the workflow with user-provided inputs, save the resulting images,
    update the job with those images, and track the job duration.
    If no datasets are associated with the job, create a temporary dataset for the user.
    """
    job = Job.objects.get(id=job_id)
    user = job.user  # Get the user associated with the job
    job.status = "running"
    start_time = now()  # Capture the start time
    job.save()

    workflow_outputs = job.workflow.outputs  # Get the workflow outputs
    additional_logs = {
        "extra_images": [],
        "extra_texts": []
    }

    try:
        # Run the workflow and get images in byte form and texts
        client_id = str(self.request.id)  # Unique client ID from Celery task
        images, texts = run_workflow(modified_workflow, job_id, client_id)
        job = Job.objects.get(id=job_id)

        # Initialize the result data
        result_data = {}

        # Find relevant prompt texts across all nodes, not just image nodes
        negative_prompt = None
        complex_prompt = None
        tag_prompt = None

        # Iterate through the workflow outputs to find the nodes that contain text prompts
        for node_id, output_info in workflow_outputs.items():
            if 'text' in output_info:
                text_type = output_info['text']
                text_value = texts.get(node_id, [''])[0]

                if text_type == 'text_prompt_negative':
                    negative_prompt = text_value
                elif text_type == 'text_prompt_complex':
                    complex_prompt = text_value
                elif text_type == 'text_prompt_tag':
                    tag_prompt = text_value

                # Save the text output in result_data
                result_data[node_id] = {
                   text_type : {
                        "type": text_type,
                        "value": text_value
                    }
                }

        # If the job has no associated datasets, create a temporary dataset for the user
        if not job.dataset:
            temp_dataset, created = Dataset.objects.get_or_create(
                name=f"Temp Dataset for {user.full_name}",
                created_by=user,
                temporary=True,  # Mark this dataset as temporary
            )
            job.dataset = temp_dataset  # Add the dataset to the job
            job.save()

        # Create a directory for the user's images
        user_dir = os.path.join(settings.MEDIA_ROOT, f"user_{user.id}")
        os.makedirs(user_dir, exist_ok=True)

        # Process images and associate them with workflow outputs
        filtered_images = {}
        for node_id, image_list in images.items():
            for idx, image_data in enumerate(image_list):
                # Convert image bytes to Image object
                image = Image.open(io.BytesIO(image_data))

                # Generate a recognizable filename
                filename = f"job_{job_id}_user_{user.id}_node_{node_id}_img_{idx}.png"
                file_path = os.path.join(user_dir, filename)

                # Save image to the media directory
                image.save(file_path)

                # Store the relative URL and create the full URL
                relative_url = os.path.relpath(file_path, settings.MEDIA_ROOT)
                full_url = os.path.join(settings.MEDIA_URL, relative_url)

                # Check if this node_id is part of the workflow outputs for images
                if node_id in workflow_outputs and 'images' in workflow_outputs[node_id]:
                    if node_id not in result_data:
                        result_data[node_id] = {}

                    # Use the workflow-determined input name for the image output
                    input_name = workflow_outputs[node_id]['images']
                    # Create DatasetImage for each image and associate text prompts
                    dataset_image = DatasetImage.objects.create(
                        job=job,
                        name=f"Generated Image {idx}",
                        image=file_path,
                        created_by=user,
                        negative_prompt=negative_prompt,  # Use the found prompts
                        complex_prompt=complex_prompt,
                        tag_prompt=tag_prompt,
                    )
                    result_data[node_id][input_name] = {
                        "id": f"{dataset_image.id}",  # Add the ID for the output image
                        "type": "image",
                        "value": full_url  # Store the full URL of the image
                    }

                    # Add to filtered images
                    if node_id not in filtered_images:
                        filtered_images[node_id] = []
                    filtered_images[node_id].append(image_data)

                else:
                    # Save the image URL to logs for non-workflow outputs
                    additional_logs['extra_images'].append({
                        "node_id": node_id,
                        "image_url": full_url
                    })

        # Handle extra texts not in workflow outputs
        for node_id, text_value in texts.items():
            if node_id not in workflow_outputs:
                additional_logs['extra_texts'].append({
                    "node_id": node_id,
                    "text": text_value
                })

        # If there are no filtered images and the job has an associated dataset image, update the existing dataset image with prompts
        if not filtered_images and job.images.exists():
            existing_image = job.images.first()
            existing_image.negative_prompt = negative_prompt
            existing_image.complex_prompt = complex_prompt
            existing_image.tag_prompt = tag_prompt
            existing_image.save()

        # Save the structured result data to the job
        job.result_data = result_data
        job.status = "completed"

        # Append the additional logs (extra texts and images)
        job.logs = (job.logs or "") + "\n" + json.dumps(additional_logs)

    except Exception as e:
        job = Job.objects.get(id=job_id)

        # In case of failure, log the error and mark job as failed
        job.status = "failed"
        job.logs = (job.logs or "") + "Error in saving task results: \n " + str(e) + "\n "

    finally:
        # Track the job duration and append to logs in proper JSON format
        end_time = now()
        job.runtime = end_time - start_time  # Store the duration in 'runtime' field

        # Append duration to logs in JSON format
        duration_log = json.dumps({
            "duration": str(job.runtime)
        })
        job.logs = (job.logs or "") + "\n" + duration_log

        job.save()  # Save job status, result, and logs

    return job_id