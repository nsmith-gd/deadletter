"""Turn rendered frame sequences into a looping GIF/MP4 or a sprite sheet.

    python assemble.py video  FRAMES_DIR OUT_STEM [--loops 4] [--width 720]
    python assemble.py sheet  FRAMES_DIR OUT.png  [--cols 6]

Needs `pip install pillow imageio-ffmpeg`.
"""
import argparse
import glob
import os
import subprocess

import imageio_ffmpeg
from PIL import Image


def frames(src):
    files = sorted(glob.glob(os.path.join(src, 'frame_*.png')))
    if not files:
        raise SystemExit(f'no frame_*.png in {src}')
    return files


def video(src, stem, loops, width):
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    first = os.path.basename(frames(src)[0])
    start = int(first[len('frame_'):-len('.png')])
    pattern = os.path.join(src, 'frame_%04d.png')
    seq = ['-framerate', '24', '-start_number', str(start), '-i', pattern]
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-stream_loop', str(loops - 1), *seq,
                    '-vf', f'scale={width}:-2:flags=lanczos', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', stem + '.mp4'], check=True)
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', *seq, '-vf',
                    f'scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=stats_mode=diff[p];'
                    '[b][p]paletteuse=dither=sierra2_4a', '-loop', '0', stem + '.gif'], check=True)


def sheet(src, out, cols):
    imgs = [Image.open(f) for f in frames(src)]
    w, h = imgs[0].size
    rows = -(-len(imgs) // cols)
    canvas = Image.new('RGBA', (cols * w, rows * h), (0, 0, 0, 0))
    for i, im in enumerate(imgs):
        canvas.paste(im, ((i % cols) * w, (i // cols) * h))
    canvas.save(out, optimize=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    v = sub.add_parser('video')
    v.add_argument('src')
    v.add_argument('stem')
    v.add_argument('--loops', type=int, default=4)
    v.add_argument('--width', type=int, default=720)
    s = sub.add_parser('sheet')
    s.add_argument('src')
    s.add_argument('out')
    s.add_argument('--cols', type=int, default=6)
    args = ap.parse_args()
    if args.cmd == 'video':
        video(args.src, args.stem, args.loops, args.width)
    else:
        sheet(args.src, args.out, args.cols)


if __name__ == '__main__':
    main()
