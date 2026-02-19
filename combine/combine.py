import argparse
import json
import os
import time
from typing import Callable, Dict, Optional

import cv2

ProgressCallback = Callable[[int, int], None]


def combine_frames(
    json_path: str,
    processed_folder: str,
    output_video: str,
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, object]:
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Timing json not found: {json_path}")
    if not os.path.isdir(processed_folder):
        raise FileNotFoundError(f"Processed image folder not found: {processed_folder}")

    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    fps = float(data.get("fps") or 24.0)
    scenes = data.get("scenes", [])

    processed_files = sorted(
        file_name
        for file_name in os.listdir(processed_folder)
        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp"))
    )

    if not processed_files:
        raise RuntimeError("No processed images found.")

    first_img_path = os.path.join(processed_folder, processed_files[0])
    first_img = cv2.imread(first_img_path)
    if first_img is None:
        raise RuntimeError(f"Unable to read first image: {first_img_path}")

    height, width, _ = first_img.shape
    os.makedirs(os.path.dirname(output_video) or ".", exist_ok=True)

    start_time = time.time()
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))

    scenes_written = 0
    for idx, scene in enumerate(scenes):
        if idx >= len(processed_files):
            break

        img_path = os.path.join(processed_folder, processed_files[idx])
        frame = cv2.imread(img_path)
        if frame is None:
            continue

        duration = int(scene.get("duration_frames", 1))
        for _ in range(max(duration, 1)):
            out.write(frame)

        scenes_written += 1
        if progress_callback is not None:
            progress_callback(scenes_written, len(scenes))

    out.release()

    elapsed_seconds = time.time() - start_time
    return {
        "timing_json": json_path,
        "processed_folder": processed_folder,
        "output_video": output_video,
        "fps": fps,
        "timing_scenes": len(scenes),
        "input_images": len(processed_files),
        "scenes_written": scenes_written,
        "elapsed_seconds": elapsed_seconds,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine processed keyframes into a video.")
    parser.add_argument("--json-path", default="timing.json", help="Path to timing json produced by extraction.")
    parser.add_argument("--processed-folder", default="processed_frames", help="Processed keyframe image directory.")
    parser.add_argument("--output-video", default="final_output.mp4", help="Output video path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = combine_frames(
        json_path=args.json_path,
        processed_folder=args.processed_folder,
        output_video=args.output_video,
    )
    print(
        "Done. Wrote "
        f"{result['scenes_written']} scenes to {result['output_video']} from {result['input_images']} images."
    )


if __name__ == "__main__":
    main()
