import argparse
import json
import os
from pathlib import Path

from src.deepfake_detection.preprocess import process_and_save


def parse_args():
    parser = argparse.ArgumentParser(description="Bulk preprocess a directory of real and fake media.")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing media files (can have subdirs like 'real', 'fake')")
    parser.add_argument("--output-dir", type=str, required=True, help="Directory to save the preprocessed .npy crops and master metadata.json")
    parser.add_argument("--target-fps", type=int, default=5, help="Frames per second to sample from videos")
    return parser.parse_args()


def get_label_from_path(file_path: Path) -> str:
    # A simple heuristic to assign label based on directory names
    path_str = str(file_path).lower()
    if "fake" in path_str or "manipulated" in path_str:
        return "Fake"
    return "Real"


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    master_metadata = []
    
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() not in {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v", ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}:
                continue
                
            print(f"Processing: {file_path}")
            try:
                arrays, metadata, _ = process_and_save(
                    input_path=file_path,
                    output_dir=output_dir,
                    target_fps=args.target_fps,
                )
                
                label = get_label_from_path(file_path)
                
                for meta in metadata:
                    meta_dict = meta.__dict__
                    meta_dict["label"] = label
                    master_metadata.append(meta_dict)
                    
            except Exception as e:
                print(f"Failed to process {file_path}: {e}")
                
    metadata_path = output_dir / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(master_metadata, f, indent=2)
        
    print(f"Bulk processing complete. Total crops extracted: {len(master_metadata)}")
    print(f"Metadata saved to: {metadata_path}")


if __name__ == "__main__":
    main()
