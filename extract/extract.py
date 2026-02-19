import argparse
import json
import os
import time
from typing import Callable, Dict, Optional

import cv2
import numpy as np

ProgressCallback = Callable[[int, int], None]


def extract_keyframes(
    video_path: str,
    output_folder: str,
    timing_json_path: str,
    threshold: int = 1_000_000,
    progress_callback: Optional[ProgressCallback] = None,
) -> Dict[str, object]:
    """
    Extract keyframes using frame-difference threshold.

    Lower threshold means higher sensitivity and more frames kept.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(os.path.dirname(timing_json_path) or ".", exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video_path}")

    start_time = time.time()
    fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    prev_frame = None
    frame_count = 0
    scene_list = []
    saved_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        is_duplicate = False
        if prev_frame is not None:
            diff = cv2.absdiff(prev_frame, gray)
            score = int(np.sum(diff))
            if score < threshold:
                is_duplicate = True

        if is_duplicate and scene_list:
            scene_list[-1]["duration_frames"] += 1
        else:
            filename = f"{saved_idx:05d}.png"
            frame_path = os.path.join(output_folder, filename)
            cv2.imwrite(frame_path, frame)
            scene_list.append({"filename": filename, "duration_frames": 1})
            prev_frame = gray
            saved_idx += 1

        if progress_callback is not None:
            progress_callback(frame_count, total_frames)

    cap.release()

    with open(timing_json_path, "w", encoding="utf-8") as file:
        json.dump({"fps": fps, "scenes": scene_list}, file, indent=2, ensure_ascii=False)

    elapsed_seconds = time.time() - start_time
    return {
        "video_path": video_path,
        "frames_dir": output_folder,
        "timing_json": timing_json_path,
        "threshold": threshold,
        "fps": fps,
        "total_frames": frame_count,
        "saved_frames": saved_idx,
        "elapsed_seconds": elapsed_seconds,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract keyframes from a video.")
    parser.add_argument("--video", default="123.mp4", help="Path to source video file.")
    parser.add_argument("--output-folder", default="extracted_frames", help="Directory for keyframes.")
    parser.add_argument("--timing-json", default="timing.json", help="Output timing json file path.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=1_000_000,
        help="Difference threshold. Lower = more sensitive, more frames.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = extract_keyframes(
        video_path=args.video,
        output_folder=args.output_folder,
        timing_json_path=args.timing_json,
        threshold=args.threshold,
    )
    print(
        "Done. Saved "
        f"{result['saved_frames']} keyframes from {result['total_frames']} frames to {result['frames_dir']}"
    )


if __name__ == "__main__":
    main()
