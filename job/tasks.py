import io
import os
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

    try:
        # Run the workflow and get images in byte form
        client_id = str(self.request.id)  # Unique client ID from Celery task
        images = run_workflow(modified_workflow, job_id, client_id)
        job = Job.objects.get(id=job_id)

        # If the job has no associated datasets, create a temporary dataset for the user
        if not job.dataset:
            temp_dataset, created = Dataset.objects.get_or_create(
                name=f"Temp Dataset for {user.full_name}",
                created_by=user,
                temporary=True,  # Mark this dataset as temporary
            )
            job.dataset=temp_dataset  # Add the dataset to the job
            job.save()

        # Create a directory for the user's images
        user_dir = os.path.join(settings.MEDIA_ROOT, f"user_{user.id}")
        os.makedirs(user_dir, exist_ok=True)

        # Save the images and store their URLs
        image_urls = []
        for node_id, image_list in images.items():
            for idx, image_data in enumerate(image_list):
                # Convert image bytes to Image object
                image = Image.open(io.BytesIO(image_data))

                # Generate a recognizable filename
                filename = f"job_{job_id}_user_{user.id}_node_{node_id}_img_{idx}.png"
                file_path = os.path.join(user_dir, filename)

                # Save image to the media directory
                image.save(file_path)

                # Store the relative URL
                relative_url = os.path.relpath(file_path, settings.MEDIA_ROOT)
                full_url = os.path.join(settings.MEDIA_URL, relative_url)
                image_urls.append(full_url)

                # Create a DatasetImage for each result image, associate with the job's dataset
                DatasetImage.objects.create(
                    job=job,
                    name=f"Generated Image {idx}",
                    image=file_path,
                    created_by=user,
                )

        # Save the result URLs to the job
        job.result_data = {"image_urls": image_urls}
        job.status = "completed"

    except Exception as e:
        job = Job.objects.get(id=job_id)

        # In case of failure, log the error and mark job as failed
        job.status = "failed"
        job.logs = (job.logs or "") + "Error in saving task results: \n " + str(e) + "\n "

    finally:
        # Track the job duration
        end_time = now()
        job.runtime = end_time - start_time  # Store the duration in 'runtime' field
        job.logs = (
            job.logs or ""
        ) + f"\nDuration: {job.runtime}\n"  # Append duration to logs
        job.save()  # Save job status, result, and logs

    return job_id
