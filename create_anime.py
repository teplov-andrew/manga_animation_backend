import os
import tempfile
import requests
import math
import random
from uuid import uuid4
from moviepy.editor import VideoFileClip, CompositeVideoClip, ColorClip, concatenate_audioclips
from s3_save_file import load_file_s3

from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.fx.audio_loop import audio_loop 

video_urls = [
    "https://fal.media/files/lion/1Uh0DkBsAv2ZVPeV91OLd_output.mp4",
    "https://fal.media/files/kangaroo/-K2BPS_nj9XJfg5SXqHAV_output.mp4",
    "https://fal.media/files/panda/tWsjI4LyXd0Bz0E5iB8P1_output.mp4",
    "https://fal.media/files/koala/JBd-FNUoK22Dj2glTlKBV_output.mp4"
    
]

music_urls = [
    "https://storage.yandexcloud.net/manymated/music/track1.mp3",
    "https://storage.yandexcloud.net/manymated/music/track2.mp3",
    "https://storage.yandexcloud.net/manymated/music/track3.mp3",
    "https://storage.yandexcloud.net/manymated/music/track4.mp3",
    "https://storage.yandexcloud.net/manymated/music/track5.mp3",
    "https://storage.yandexcloud.net/manymated/music/track6.mp3"
]
 


def download_video(url: str) -> str:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    for chunk in response.iter_content(8192):
        if chunk:
            tmp_file.write(chunk)
    tmp_file.close()
    return tmp_file.name

def download_audio(url: str) -> str:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    for chunk in response.iter_content(8192):
        if chunk:
            tmp_file.write(chunk)
    tmp_file.close()
    return tmp_file.name


def add_background_music(clip: VideoFileClip, audio_url: str, volume: float = 1.0) -> VideoFileClip:
    audio_path = download_audio(audio_url)
    base_audio = AudioFileClip(audio_path)

    if base_audio.duration < clip.duration - 1e-3:
        n = math.ceil(clip.duration / base_audio.duration)
        bgm = concatenate_audioclips([base_audio] * n).subclip(0, clip.duration)
    else:
        bgm = base_audio.subclip(0, clip.duration)

    bgm = bgm.volumex(volume).set_duration(clip.duration)
    return clip.set_audio(bgm) 

def _scale_clip(clip: VideoFileClip, canvas_w: int, canvas_h: int, limit: float = 1.5) -> VideoFileClip:
    scale = min(limit, canvas_w / clip.w, canvas_h / clip.h)
    return clip if scale == 1 else clip.resize(scale)

def create_anime(urls: list[str], transition: float = 0.25, music_url: str | None = None, music_volume: float = 1.0) -> dict:
    CANVAS_WIDTH, CANVAS_HEIGHT = 1080, 1920 
    raw_clips = [VideoFileClip(download_video(u)) for u in urls]

    overlap = max(0, len(raw_clips) - 1) * transition
    total_duration = sum(c.duration for c in raw_clips) - overlap

    background = (
        ColorClip((CANVAS_WIDTH, CANVAS_HEIGHT), color=(255, 255, 255))
        .set_duration(total_duration)
    )

    layers = []
    current_t = 0.0 

    for idx, clip in enumerate(raw_clips):
        clip = _scale_clip(clip, CANVAS_WIDTH, CANVAS_HEIGHT)

        if idx == 0:
            main = clip.subclip(0, clip.duration - transition)
            layers.append(main.set_start(current_t).set_position(('center', 'center')))
            current_t += clip.duration - transition
            continue

        direction = random.choice(['right', 'left', 'down', 'up'])

        prev_clip = _scale_clip(raw_clips[idx - 1], CANVAS_WIDTH, CANVAS_HEIGHT)
        prev_tail = prev_clip.subclip(prev_clip.duration - transition)
        next_head = clip.subclip(0, transition)

        if direction == 'right':
            prev_pos = lambda t: (CANVAS_WIDTH * (t / transition), 'center')
            next_pos = lambda t: (-CANVAS_WIDTH + CANVAS_WIDTH * (t / transition), 'center')
        elif direction == 'left':
            prev_pos = lambda t: (-CANVAS_WIDTH * (t / transition), 'center')
            next_pos = lambda t: (CANVAS_WIDTH - CANVAS_WIDTH * (t / transition), 'center')
        elif direction == 'down':
            prev_pos = lambda t: ('center', CANVAS_HEIGHT * (t / transition))
            next_pos = lambda t: ('center', -CANVAS_HEIGHT + CANVAS_HEIGHT * (t / transition))
        else: 
            prev_pos = lambda t: ('center', -CANVAS_HEIGHT * (t / transition))
            next_pos = lambda t: ('center', CANVAS_HEIGHT - CANVAS_HEIGHT * (t / transition))

        slide_prev = prev_tail.set_start(current_t).set_position(prev_pos)
        slide_next = next_head.set_start(current_t).set_position(next_pos)
        main_next = (
            clip.subclip(transition)
            .set_start(current_t + transition)
            .set_position(('center', 'center'))
        )

        layers.extend([slide_prev, slide_next, main_next])
        current_t += clip.duration - transition

    final = CompositeVideoClip([background, *layers], size=(CANVAS_WIDTH, CANVAS_HEIGHT))
    
    if music_url:
        final = add_background_music(final, music_url, music_volume)

    output_name = f'vertical_final_{uuid4()}.mp4'
    final.write_videofile(
        output_name,
        codec='libx264',
        preset='slow',
        ffmpeg_params=['-crf', '18'],
        audio_codec='aac',
    )

    url = load_file_s3(output_name)

    for c in raw_clips:
        if hasattr(c, 'filename') and os.path.exists(c.filename):
            os.remove(c.filename)
    if os.path.exists(output_name):
        os.remove(output_name)

    return {'file_url': url, 'file_name': output_name}


if __name__ == '__main__':
    print(create_anime(video_urls, music_url=music_urls[0]))
