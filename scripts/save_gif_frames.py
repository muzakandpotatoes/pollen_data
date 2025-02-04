"""
Extract frames from GIF animations and save them in an organized directory structure for web display.

This script takes GIF animations and extracts individual frames as PNG files, organizing them into
subdirectories by animation name. It's designed to prepare animations for web viewing with frame-by-frame
control.

The frames are saved in the following structure:
   public/
   └── frames/
       └── {animation_name}/
           ├── frame_000.png
           ├── frame_001.png
           └── ...

The script handles GIF color palette conversion and creates directories as needed. Frame numbering
starts at 000 and uses zero-padding to ensure correct ordering when loaded by the web application.
"""

import argparse
import os

from PIL import Image


def extract_gif_frames(gif_path, animation_name):
    # Create nested directory structure
    output_dir = os.path.join("webpage", "public", "frames", animation_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with Image.open(gif_path) as gif:
        n_frames = getattr(gif, "n_frames", 1)

        for frame in range(n_frames):
            gif.seek(frame)
            frame_image = gif.convert("RGB") if gif.mode == "P" else gif
            frame_image.save(os.path.join(output_dir, f"frame_{frame:03d}.png"))

        print(f"Extracted {n_frames} frames to {output_dir}")
        return n_frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gif_path",
        default="pollen_animation_2024-06-07_2025-02-02_lowess_cloughtocher_20hz.gif",
        help="Path to the input GIF file",
    )
    parser.add_argument(
        "--animation_name",
        default="lowess",
        help="Name of the animation subdirectory to create",
    )
    args = parser.parse_args()

    num_frames = extract_gif_frames(args.gif_path, args.animation_name)
    print(f"Successfully extracted {num_frames} frames")


if __name__ == "__main__":
    main()
