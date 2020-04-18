import yaml
import pandas as pd
import argparse as arg
import parse_video as vid
import os
from datetime import datetime
import shutil


if __name__=="__main__":
    parser = arg.ArgumentParser(description='calculate pixel changes in a video frame by frame')
    parser.add_argument('-f', '--filename', type=str, help='avi file', action="store", default=None)
    parser.add_argument('-d', '--directory', type=str, help="directory of avi files and nothing else", default=None)
    parser.add_argument('-y', '--config_yaml', type=str, help='path of the config.yaml file', action="store")
    parser.add_argument('-e', '--extension', type=str, help='file extension default .avi', action="store", default=".avi")
    parser.add_argument('-o', '--output', type=str, help='name of the output directory, this will have subdirectories', action="store")
    args = parser.parse_args()

    if args.filename is not None and args.directory is not None:
        raise ValueError("You need to specify either filename or directory not both")

    if args.config_yaml is None:
        raise FileNotFoundError("You need to specify a config file for pipeline parameters")


    with open(args.config_yaml) as f:
        params=yaml.safe_load(f)

    files=[]
    if args.filename is not None:
        files.append(args.filename)

    if args.directory is not None:
        files=[]
        for file in os.listdir(args.directory):
            if file.endswith(args.extension):
                files.append(args.directory+"/"+file)
            else:
                continue

    parsed_videos={}
    for file in files:
        print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Parsing frames for "+ file)
        parsed_videos[file]={"intensity":[], "masks":[]}
        myvid=vid.Video(path=file)

        gen=vid.frame_generator(invert=params['invert_frame'])
        if params['method'] == 'background':
            backsub=vid.subtractor(algo=params['algorithm'], **params['method_parameters'])
            frames, masks = vid.movement_by_background_removal(backsub, gen,
                                                               invert_mask=params['invert_mask'],
                                                               **params['apply_parameters'])
            zippedList = list(zip(range(len(masks)), [mask.sum() for mask in masks]))
            results = pd.DataFrame(zippedList, columns=['frame', 'movement'])
        elif params['method'] == 'flow':
            pass
        else:
            raise ValueError("""method must be either flow for optical flow or background for
                             background removal""")


        name = file.replace(" ", "_").replace(args.extension, "")
        name = name.split("/").pop()

        resultsdir=args.output+"/"+name

        os.makedirs(resultsdir, exist_ok=True)
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating excel file for " + file)
        with pd.ExcelWriter(resultsdir+"/results.xlsx") as writer:
            raw.to_excel(writer, sheet_name="raw_data", index=False)
            normalized.to_excel(writer, sheet_name="reference_removed", index=False)

        if params["video"]["write"]:
            print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating mp4 files for " + file)
            for type in params["video"]["what"]:
                myvid.write_mp4(frames=frames, masks=masks, what=type, outpath=resultsdir,
                                size=(params["video"]["size"]["width"],params["video"]["size"]["height"]),
                                FPS=params["video"]["FPS"], period=params["video"]["periodicity"])

        shutil.copy(args.config_yaml, resultsdir+"/config.yaml")
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + file + " done!")



