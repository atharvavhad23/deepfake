#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import urllib
import urllib.request
import tempfile
from os.path import join

SERVER_URL = 'http://kaldir.vc.in.tum.de/FaceForensics/'
BASE_URL = SERVER_URL + 'v1_cargo/'
ORIGINAL_VIDEOS_URL = BASE_URL + 'original_videos.tar.gz'
DATASET_TYPES = ["raw", "compressed", "selfreenactment_raw", "selfreenactment_compressed", "original_videos", "selfreenactment_images", "source_to_target_images"]
NUM_SAMPLES=5

def get_filelist(filelist_url):
    lines = urllib.request.urlopen(filelist_url)
    video_filenames = []
    for line in lines:
        video_filenames.append(line.decode('utf-8').rstrip('\n'))
    return video_filenames

def download_files(filenames, base_url, output_path, sample_only=False):
    os.makedirs(output_path, exist_ok=True)
    num_filenames=len(filenames) if not sample_only else NUM_SAMPLES
    for i, filename in enumerate(filenames):
        try:
            download_file(base_url + filename, join(output_path, filename))
        except Exception as e:
            print(f"WARNING: failed to download {filename} ({e}). Skipping.")
        if sample_only and i != 0 and i % (NUM_SAMPLES - 1) == 0: break

def download_file(url, out_file):
    out_dir = os.path.dirname(out_file)
    os.makedirs(out_dir, exist_ok=True)
    if not os.path.isfile(out_file):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                with open(out_file, 'wb') as f:
                    while True:
                        block = response.read(16384)
                        if not block:
                            break
                        f.write(block)
        except Exception as e:
            if os.path.isfile(out_file):
                try:
                    os.remove(out_file)
                except Exception:
                    pass
            raise e

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output_path')
    parser.add_argument('-d', '--dataset_type', default='compressed')
    parser.add_argument('--sample_only', action='store_true')
    args = parser.parse_args()

    if args.dataset_type == 'original_videos':
        download_file(ORIGINAL_VIDEOS_URL, out_file=join(args.output_path, 'faceforensics_original_videos.tar.gz'))
    else:
        folder = 'train'
        filelist_url = BASE_URL + 'source_to_target/filelists/{}.txt'.format(folder)
        filenames = get_filelist(filelist_url)
        output_path = join(args.output_path, 'FaceForensics_{}'.format(args.dataset_type), folder, 'altered')
        base_url = BASE_URL + 'source_to_target/compressed/{}/altered/'.format(folder)
        download_files(filenames, base_url, output_path=output_path, sample_only=args.sample_only)

if __name__ == "__main__":
    main()
