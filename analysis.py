import yaml
import pandas as pd
import argparse as arg
import video as vid
import os
from datetime import datetime
import shutil

if __name__=="__main__":
    parser = arg.ArgumentParser(description='detect objects or movements in a video file')
    parser.add_argument('-f', '--filename', type=str, help='avi file', action="store", default=None)
    parser.add_argument('-d', '--directory', type=str, help="directory of avi files and nothing else", default=None)
    parser.add_argument('-y', '--config_yaml', type=str, help='path of the config.yaml file', action="store")
    parser.add_argument('-e', '--extension', type=str, help='file extension default .avi', action="store", default=".avi")
    parser.add_argument('-o', '--output', type=str, help='name of the output directory, this will have subdirectories', action="store")
    args = parser.parse_args()

    if args.config_yaml is None:
        raise FileNotFoundError("You need to specify a config file for pipeline parameters")

    with open(args.config_yaml) as f:
        params = yaml.safe_load(f)

    if args.filename is not None and args.directory is not None:
        raise ValueError("You need to specify either filename or directory not both")

    files = []
    if args.filename is not None:
        files.append(args.filename)

    if args.directory is not None:
        files = []
        for file in os.listdir(args.directory):
            if file.endswith(args.extension):
                files.append(args.directory + "/" + file)
                print(files)
            else:
                continue

    parsed_videos = {}
    for file in files:
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Parsing frames for " + file)
        myvid = vid.Video(path=file)
        myvid.get_frames(invert=params["invert"], denoise=params["denoice"], dsk=params["disk_size"])

        if params["method"]=="object_detection":
            from video_parser import object

        elif params["method"]=="movement_detection"
            from video_parser import movement
            pass



