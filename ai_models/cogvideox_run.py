import subprocess
import os
import sys
from uuid import uuid4
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from s3_save_file import load_file_s3


def cogvideox_generate(
    prompt: str,
    image_or_video_path: str,
    model_path: str,
    lora_path: str,
    generate_type: str = "i2v",
    num_frames: int = 16,
    output_path: str = f"./output_{str(uuid4())}.mp4"
) -> str:
    command = [
        "python", "/manga_animation_backend/CogVideo/inference/cli_demo.py",
        "--prompt", prompt,
        "--image_or_video_path", image_or_video_path,
        "--model_path", model_path,
        "--lora_path", lora_path,
        "--generate_type", generate_type,
        "--num_frames", str(num_frames),
        "--output_path", output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    try:
        url = load_file_s3(output_path)
        return {'file_url': url, 'file_name': output_path}
    except:
        print(output_path)
    
if __name__ == '__main__':
    video_path = cogvideox_generate(
        prompt="a anime boy is talking",
        image_or_video_path="/manga_animation_backend/CogVideo/img2.png",
        model_path="THUDM/CogVideoX1.5-5B-I2V",
        lora_path="/workspace/manga_animation_backend/CogVideo/checkpoint/ephemeral/CogVideo/my_output3/checkpoint-1050",
        generate_type="i2v",
        num_frames=16,
    )
    
    print("Сгенерированное видео:", video_path)
