import yaml
import pandas as pd
import argparse as arg
import parse_video as vid
import os
from datetime import datetime


if __name__=="__main__":
    parser = arg.ArgumentParser(description='calculate pixel changes in a video frame by frame')
    parser.add_argument('-f', '--filename', type=str, help='avi file', action="store", default=None)
    parser.add_argument('-d', '--directory', type=str, help="directory of avi files and nothing else", default=None)
    parser.add_argument('-t', '--use_object_tracking', help="use feature and geometry matching", default=False,
                        action='store_true')
    parser.add_argument('-y', '--config_yaml', type=str, help='path of the config.yaml file', action="store")
    parser.add_argument('-c', '--cores', type=int, help='number of cores to use (integer)', action="store", default=1)
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
            if file.endswith(".avi"):
                files.append(args.directory+"/"+file)
            else:
                continue

    parsed_videos={}
    for file in files:
        print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Parsing frames for "+ file)
        parsed_videos[file]={"intensity":[], "masks":[]}
        myvid=vid.Video(path=file)
        myvid.get_frames(return_denoised=params["frames"]["return_denoized"],
                              dsk_size=params["frames"]["disk_size"],
                              invert=params["frames"]["invert"])
        print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Detecting objects for  " + file)
        masks=myvid.get_masks(myvid.frames, cores=args.cores, quant=params["masks"]["quantile"])
        if args.use_object_tracking:
            print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Object tracking for " + file)
            warped_frames, warped_masks=myvid.track_object(myvid.frames, masks, cores=args.cores,
                                                           min=params["tracking"]["min"],
                                                           norm=params["tracking"]["normalize"],
                                                           reference_frame=params["tracking"]["reference_frame"])
            print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Calculating values for " + file)
            mask_area, frame_intensities = myvid.calculate_values(warped_frames, warped_masks,
                                                                  remove_background=params["calculate"][
                                                                      "remove_background"])
        else:
            print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"Calculating values for " + file)
            mask_area, frame_intensities=myvid.calculate_values(myvid.frames, masks,
                                                                remove_background=params["calculate"]["remove_background"])
        parsed_videos[file]["intensity"]=frame_intensities
        parsed_videos[file]["masks"] = mask_area

        if len(params["calculate"]["attributes"]) > 0:
            print("["+datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"] "+"calculating attributes for "+ file)
            raw=myvid.calculate_measures(masks, myvid.frames, params["calculate"]["attributes"], args.cores,
                                     params["calculate"]["cache"])

            raw.insert(0, "masks", parsed_videos[file]["masks"])
            raw.insert(1, "intensity", parsed_videos[file]["intensity"])

        else:
            raw=pd.DataFrame(parsed_videos[file])

        noref=[]
        for column in raw.columns.values:
            col_noref= raw[column] - raw[column][params["tracking"]["reference_frame"]]
            noref.append(col_noref)

        normalized=pd.concat(noref, axis=1)

        resultsdir=args.output+"/"+file

        os.mkdir(resultsdir)
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating excel file for " + file)
        with pd.ExcelWriter(resultsdir+"/results.xlsx") as writer:
            raw.to_excel(writer, sheet_name="raw_data", index=False)
            normalized.to_excel(writer, sheet_name="reference_removed", index=False)

        if params["video"]["write"]:
            print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "generating mp4 files for " + file)
            for type in params["video"]["what"]:
                myvid.write_mp4(frames=myvid.frames, masks=masks, what=type, outpath=resultsdir,
                                size=(params["video"]["size"]["width"],params["video"]["size"]["height"]),
                                FPS=params["video"]["FPS"], period=params["video"]["periodicity"])

        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + file + " done!")



