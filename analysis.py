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

    if args.config_yaml is None:
        raise FileNotFoundError("You need to specify a config file for pipeline parameters")

    with open(args.config_yaml) as f:
        params = yaml.safe_load(f)

    if args.filename is not None and args.directory is not None:
        raise ValueError("You need to specify either filename or directory not both")

    files=[]
    if args.filename is not None:
        files.append(args.filename)

    if args.directory is not None:
        files=[]
        for file in os.listdir(args.directory):
            if file.endswith(args.extension):
                files.append(args.directory+"/"+file)
                print(files)
            else:
                continue

    parsed_videos={}
    for file in files:
        print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Parsing frames for "+ file)
        myvid=vid.Video(path=file)

        gen=myvid.frame_generator(invert=params['invert_frame'])

        if params['method']=="background_remove":
            backsub=myvid.subtractor(algo=params['algorithm'], **params['method_parameters'])
            frames, masks = myvid.movement_by_background_removal(backsub, gen,
                                                               invert_mask=params['invert_mask'],
                                                               **params['apply_parameters'])
            zippedList = list(zip(range(len(masks)), [mask.sum() for mask in masks]))
            results = pd.DataFrame(zippedList, columns=['frame', 'movement'])

        elif params['method']=="optical_flow":
            pass

        else:
            raise ValueError("method needs to be either optical_flow or background_remove")

        name = file.replace(" ", "_").replace(args.extension, "")
        name = name.split("/").pop()

        resultsdir=args.output+"/"+name

        os.makedirs(resultsdir, exist_ok=True)
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating excel file for " + file)
        with pd.ExcelWriter(resultsdir+"/results.xlsx") as writer:
            results.to_excel(writer, sheet_name="results", index=False)


        if params["video"]["write"]:
            print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating mp4 files for " + file)
            myvid.write_mp4(frames=frames, masks=masks, output=resultsdir+"/analysis.mp4",
                            size=(params["video"]["size"]["width"],params["video"]["size"]["height"]),
                            FPS=params["video"]["FPS"], period=params["video"]["periodicity"])

        shutil.copy(args.config_yaml, resultsdir+"/config.yaml")
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + file + " done!")



