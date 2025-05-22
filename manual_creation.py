from moviepy.editor import ImageClip, CompositeVideoClip, vfx, ColorClip
from moviepy.video.VideoClip import VideoClip
import numpy as np
from PIL import Image
from uuid import uuid4
from s3_save_file import load_file_s3
from io import BytesIO
import os



class Manual:
    def __init__(self, image_array: np.ndarray):
        self.input_file = image_array
        self.output_file = f"manual_settings_{str(uuid4())}.mp4"
        
    def reveal(self, duration=3, fps=30):
        h, w = self.input_file.shape[:2]
        img_clip = ImageClip(self.input_file).set_duration(duration)         

        def make_mask(t):
            progress = np.clip(t / duration, 0, 1)

            gradient = np.tile(np.linspace(0, 1, w), (h, 1))
            mask_frame = (gradient < progress).astype(float)  
            return mask_frame

        mask_clip = VideoClip(lambda t: make_mask(t),
                      ismask=True,
                      duration=duration).set_fps(fps)
        img_clip = img_clip.set_mask(mask_clip)
        
        bg = ColorClip(size=(w, h), color=(255, 255, 255)).set_duration(duration)

        final = CompositeVideoClip([bg, img_clip])
        w, h = final.size
        if w % 2 or h % 2:
            final = final.resize(((w // 2) * 2, (h // 2) * 2))
    
        final.write_videofile(self.output_file,
                            codec="libx264",
                            fps=fps,
                            audio=False) 
        
        url = load_file_s3(self.output_file)
        
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        
        return {"file_url": url, "file_name": self.output_file}
    


    def zoom(self, duration: float = 3.0, fps: int = 120, start_scale: float = 0.7, end_scale: float = 1.0, upscale: int = 2):
        H, W = self.input_file.shape[:2]
        img_clip = ImageClip(self.input_file).set_duration(duration)
        def smootherstep(x: float) -> float:
            return 6*x**5 - 15*x**4 + 10*x**3

        def scale(t: float) -> float:
            prog = smootherstep(t / duration)
            return start_scale + (end_scale - start_scale) * prog

        def position(t: float):
            s = scale(t)
            w_new, h_new = W * s * upscale, H * s * upscale
            return ((W*upscale - w_new) / 2,
                    (H*upscale - h_new) / 2)
            
        zoom_hi = (img_clip.resize(lambda t: scale(t) * upscale).set_position(position))

        bg_hi = ColorClip(size=(W*upscale, H*upscale), color=(255,255,255))\
                    .set_duration(duration)

        final_hi = CompositeVideoClip(
            [bg_hi, zoom_hi],
            size=(W*upscale, H*upscale)
        ).set_fps(fps)

        def downscale_frame(frame: np.ndarray) -> np.ndarray:
            img = Image.fromarray(frame)
            return np.array(img.resize((W, H), Image.LANCZOS))

        final = final_hi.fl_image(downscale_frame).set_fps(fps)

        w2, h2 = final.size
        if w2 % 2 or h2 % 2:
            final = final.resize(((w2//2)*2, (h2//2)*2))

        final.write_videofile(self.output_file, codec="libx264", fps=fps, audio=False, preset="slow", ffmpeg_params=["-pix_fmt", "yuv420p"])

        url = load_file_s3(self.output_file)
        
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        
        return {"file_url": url, "file_name": self.output_file}
    
    def shake(self, duration: float = 3.0, fps: int = 30, max_angle: float = 1.0, frequency: float = 1.0):

        H, W = self.input_file.shape[:2]
        img_clip = ImageClip(self.input_file).set_duration(duration)

        angle_fn = lambda t: max_angle * np.sin(2 * np.pi * frequency * t)

        rotate_clip = img_clip.rotate(angle_fn, resample="bilinear", expand=False)
        shake_clip = rotate_clip.set_position("center")

        bg = ColorClip(size=(W, H), color=(255, 255, 255)).set_duration(duration)
        final = CompositeVideoClip([bg, shake_clip], size=(W, H))
        
        w2, h2 = final.size
        if w2 % 2 or h2 % 2:
            final = final.resize(((w2 // 2) * 2, (h2 // 2) * 2))

        final.write_videofile(self.output_file, codec="libx264", fps=fps, audio=False)
        url = load_file_s3(self.output_file)
        
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
            
        return {"file_url": url, "file_name": self.output_file}


if __name__ == '__main__':
    print(Manual(np.array(Image.open("/Users/andrew/Documents/img6.png").convert("L").convert("RGB"))).zoom())
        
    
    