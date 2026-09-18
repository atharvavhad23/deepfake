#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import os
import urllib
import urllib.request
import tempfile
import time
import sys
import json
import random
from tqdm import tqdm
from os.path import join

FILELIST_URL = 'misc/filelist.json'
DEEPFEAKES_DETECTION_URL = 'misc/deepfake_detection_filenames.json'
DEEPFAKES_MODEL_NAMES = ['decoder_A.h5', 'decoder_B.h5', 'encoder.h5',]

DATASETS = {
    'original_youtube_videos': 'misc/downloaded_youtube_videos.zip',
    'original_youtube_videos_info': 'misc/downloaded_youtube_videos_info.zip',
    'original': 'original_sequences/youtube',
    'DeepFakeDetection_original': 'original_sequences/actors',
    'Deepfakes': 'manipulated_sequences/Deepfakes',
    'DeepFakeDetection': 'manipulated_sequences/DeepFakeDetection',
    'Face2Face': 'manipulated_sequences/Face2Face',
    'FaceShifter': 'manipulated_sequences/FaceShifter',
    'FaceSwap': 'manipulated_sequences/FaceSwap',
    'NeuralTextures': 'manipulated_sequences/NeuralTextures'
    }
ALL_DATASETS = ['original', 'DeepFakeDetection_original', 'Deepfakes',
                'DeepFakeDetection', 'Face2Face', 'FaceShifter', 'FaceSwap',
                'NeuralTextures']
COMPRESSION = ['raw', 'c23', 'c40']
TYPE = ['videos', 'masks', 'models']
SERVERS = ['EU', 'EU2', 'CA']

def parse_args():
    parser = argparse.ArgumentParser(
        description='Downloads FaceForensics v2 public data release.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('output_path', type=str, help='Output directory.')
    parser.add_argument('-d', '--dataset', type=str, default='all',
                        choices=list(DATASETS.keys()) + ['all']
                        )
    parser.add_argument('-c', '--compression', type=str, default='raw',
                        choices=COMPRESSION
                        )
    parser.add_argument('-t', '--type', type=str, default='videos',
                        choices=TYPE
                        )
    parser.add_argument('-n', '--num_videos', type=int, default=None,
                        help='Select a number of videos to download.')
    parser.add_argument('--server', type=str, default='EU',
                        choices=SERVERS
                        )
    args = parser.parse_args()

    server = args.server
    if server == 'EU':
        server_url = 'http://canis.vc.in.tum.de:8100/'
    elif server == 'EU2':
        server_url = 'http://kaldir.vc.in.tum.de/faceforensics/'
    elif server == 'CA':
        server_url = 'http://falas.cmpt.sfu.ca:8100/'
    else:
        raise Exception('Wrong server name.')
    args.tos_url = server_url + 'webpage/FaceForensics_TOS.pdf'
    args.base_url = server_url + 'v3/'
    args.deepfakes_model_url = server_url + 'v3/manipulated_sequences/Deepfakes/models/'

    return args

def download_files(filenames, base_url, output_path, report_progress=True):
    os.makedirs(output_path, exist_ok=True)
    if report_progress:
        filenames = tqdm(filenames)
    for filename in filenames:
        try:
            download_file(base_url + filename, join(output_path, filename))
        except Exception as e:
            tqdm.write(f"WARNING: failed to download {filename} ({e}). Skipping.")

def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = int(count * block_size * 100 / total_size)
    sys.stdout.write("\rProgress: %d%%, %d MB, %d KB/s" % (percent, progress_size / (1024 * 1024), speed))
    sys.stdout.flush()

def download_file(url, out_file, report_progress=False):
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
    else:
        tqdm.write('WARNING: skipping download of existing file ' + out_file)

def main(args):
    c_datasets = [args.dataset] if args.dataset != 'all' else ALL_DATASETS
    c_type = args.type
    c_compression = args.compression
    num_videos = args.num_videos
    output_path = args.output_path

    for dataset in c_datasets:
        dataset_path = DATASETS[dataset]
        if 'original_youtube_videos' in dataset:
            download_file(args.base_url + '/' + dataset_path, out_file=join(output_path, 'downloaded_videos.zip'), report_progress=True)
            return

        if 'DeepFakeDetection' in dataset_path or 'actors' in dataset_path:
        	filepaths = json.loads(urllib.request.urlopen(args.base_url + '/' + DEEPFEAKES_DETECTION_URL).read().decode("utf-8"))
        	filelist = filepaths['actors'] if 'actors' in dataset_path else filepaths['DeepFakesDetection']
        elif 'original' in dataset_path:
            file_pairs = json.loads(urllib.request.urlopen(args.base_url + '/' + FILELIST_URL).read().decode("utf-8"))
            filelist = []
            for pair in file_pairs: filelist += pair
        else:
            file_pairs = json.loads(urllib.request.urlopen(args.base_url + '/' + FILELIST_URL).read().decode("utf-8"))
            filelist = []
            for pair in file_pairs:
                filelist.append('_'.join(pair))
                if c_type != 'models': filelist.append('_'.join(pair[::-1]))
        if num_videos is not None and num_videos > 0:
        	filelist = filelist[:num_videos]

        dataset_videos_url = args.base_url + '{}/{}/{}/'.format(dataset_path, c_compression, c_type)
        dataset_mask_url = args.base_url + '{}/{}/videos/'.format(dataset_path, 'masks', c_type)

        if c_type == 'videos':
            dataset_output_path = join(output_path, dataset_path, c_compression, c_type)
            filelist = [filename + '.mp4' for filename in filelist]
            download_files(filelist, dataset_videos_url, dataset_output_path)
        elif c_type == 'masks':
            dataset_output_path = join(output_path, dataset_path, c_type, 'videos')
            if 'original' in dataset or 'FaceShifter' in dataset: continue
            filelist = [filename + '.mp4' for filename in filelist]
            download_files(filelist, dataset_mask_url, dataset_output_path)

if __name__ == "__main__":
    args = parse_args()
    main(args)
