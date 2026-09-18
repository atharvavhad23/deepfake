from __future__ import annotations

import argparse
from pathlib import Path

from src.deepfake_detection.data import extract_video_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract frames from a video")
    parser.add_argument("--video", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--frame-stride", type=int, default=30)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = extract_video_frames(args.video, args.output_dir, frame_stride=args.frame_stride)
    print(f"Saved {count} frames to {Path(args.output_dir)}")


if __name__ == "__main__":
    main()
