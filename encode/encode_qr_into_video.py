import cv2
import qrcode
import numpy as np
from moviepy.editor import VideoFileClip, ImageSequenceClip

def generate_qr(data: str, size: int = 100):
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((size, size))
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)

def encode_video_with_qr(input_video: str, output_video: str, data: str, position=(10, 10)):
    clip = VideoFileClip(input_video)
    frames = []
    qr_img = generate_qr(data, size=100)
    h, w, _ = qr_img.shape

    for frame in clip.iter_frames():
        frame = frame.copy()
        try:
            frame[position[1]:position[1]+h, position[0]:position[0]+w] = qr_img
        except ValueError:
            continue
        frames.append(frame)

    new_clip = ImageSequenceClip(frames, fps=clip.fps)
    new_clip.write_videofile(output_video, codec='libx264')

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Uso: encode_qr_into_video.py input.mp4 output.mp4 'Texto o QR'")
        sys.exit(1)
    _, inp, outp, data = sys.argv
    encode_video_with_qr(inp, outp, data)