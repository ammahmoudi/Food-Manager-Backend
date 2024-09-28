from job.tasks import run_workflow_task
run_workflow_task(job_id=1, modified_workflow={
  "3": {
      "class_type": "KSampler",
      "inputs": {
          "cfg": 8,
          "denoise": 1,
          "latent_image": [
              "5",
              0
          ],
          "model": [
              "4",
              0
          ],
          "negative": [
              "7",
              0
          ],
          "positive": [
              "6",
              0
          ],
          "sampler_name": "euler",
          "scheduler": "normal",
          "seed": 8566257,
          "steps": 20
      }
  },
  "4": {
      "class_type": "CheckpointLoaderSimple",
      "inputs": {
          "ckpt_name": "mdjrny-v4.safetensors"
      }
  },
  "5": {
      "class_type": "EmptyLatentImage",
      "inputs": {
          "batch_size": 1,
          "height": 512,
          "width": 512
      }
  },
  "6": {
      "class_type": "CLIPTextEncode",
      "inputs": {
          "clip": [
              "4",
              1
          ],
          "text": "masterpiece best quality boy"
      }
  },
  "7": {
      "class_type": "CLIPTextEncode",
      "inputs": {
          "clip": [
              "4",
              1
          ],
          "text": "bad hands"
      }
  },
  "8": {
      "class_type": "VAEDecode",
      "inputs": {
          "samples": [
              "3",
              0
          ],
          "vae": [
              "4",
              2
          ]
      }
  },
  "9": {
      "class_type": "SaveImage",
      "inputs": {
          "filename_prefix": "ComfyUI",
          "images": [
              "8",
              0
          ]
      }
  }
})
