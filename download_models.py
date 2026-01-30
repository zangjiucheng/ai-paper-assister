#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple downloader for MinerU / Magic-PDF models and config update.
"""

import json
import os

import requests
from modelscope import snapshot_download


def download_json(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def download_and_modify_json(url, local_filename, modifications):
    if os.path.exists(local_filename):
        with open(local_filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            config_version = data.get('config-version', '0.0.0')
            if config_version < '1.2.0':
                print(f'Updating config-version from {config_version} to 1.2.0')
                data = download_json(url)
    else:
        data = download_json(url)

    for key, value in modifications.items():
        data[key] = value

    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    mineru_patterns = [
        "models/Layout/YOLO/*",
        "models/MFD/YOLO/*",
        "models/MFR/unimernet_hf_small_2503/*",
        "models/OCR/paddleocr_torch/*",
    ]
    model_dir = snapshot_download('OpenDataLab/PDF-Extract-Kit-1.0', allow_patterns=mineru_patterns)
    layoutreader_model_dir = snapshot_download('ppaanngggg/layoutreader')
    model_dir = model_dir + '/models'
    print(f'model_dir is: {model_dir}')
    print(f'layoutreader_model_dir is: {layoutreader_model_dir}')

    json_url = 'https://gcore.jsdelivr.net/gh/opendatalab/MinerU@magic_pdf-1.3.12-released/magic-pdf.template.json'
    config_file_name = 'magic-pdf.json'
    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, config_file_name)

    json_mods = {
        'models-dir': model_dir,
        'layoutreader-model-dir': layoutreader_model_dir,
        'device-mode': 'mps',
    }

    download_and_modify_json(json_url, config_file, json_mods)
    print(f'The configuration file has been configured successfully, the path is: {config_file}')
