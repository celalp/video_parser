import yaml
import pandas as pd
import argparse as arg
import parse_video as vid
from plotnine import
import os


if __name__=="__main__":
    parser = arg.ArgumentParser(description='calculate pixel changes in a video frame by frame')
    parser.add_argument('-f', '--filename', type=str, help='avi file', action="store", default=None)
    parser.add_argument('-d', '--directory', type=str, help="directory of avi files and nothing else", default=None)
    parser.add_argument('-t', '--use_object_tracking', help="use feature and geometry matching", default=False,
                        action='store_true')
    parser.add_argument('-c', '--config_file', type=str, help='path of the config.yaml file', action="store")
    parser.add_argument('-t', '--threads', type=int, help='number of cores to use (integer)', action="store", default=1)
    parser.add_argument('-o', '--output', type=str, help='name of the output file', action="store")
    parser.add_argument('-p', '--plot_results', type=str, help='plot results', action="store_true")
    parser.add_argument()
    args = parser.parse_args()

    if args.filename is not None and args.directory is not None:
        ValueError("You need to specify either filename or directory not both")

    if args.config_file is None:
        FileNotFoundError("You need to specify a config file for pipeline parameters")


    with open(args.config_file) as f:
        params=yaml.safe_load(f)


    if args.filename:
        files=args.filename

    if args.directory:
        files=[]
        for file in os.listdir(args.directory):
            if file.endswith(".avi"):
                files.append(args.directory+"/"+file)
            else:
                continue

    parsed_videos={}
    for file in files:
        parsed_videos[file]={"frames":[], "masks":[]}
        myvid=vid.Video(file)
        myvid.get_frames(return_denoised=params["frames"]["return_denoized"],
                              dsk_size=params["frames"]["disk_size"],
                              invert=params["frames"]["invert"])
        masks=myvid.get_masks(cores=args.threads, quant=params["masks"]["quant"])
        if args.use_object_tracking:
            warped_frames, warped_masks=myvid.track_object(myvid.frames, masks, cores=args.threads,
                                                           min=params["tracking"]["min"],
                                                           norm=params["tracking"]["normalize"],
                                                           reference_frame=params["tracking"]["reference_frame"])
            mask_area, frame_intensities = myvid.calculate_values(warped_frames, warped_masks,
                                                                  remove_background=params["calculate"][
                                                                      "remove_background"])
        else:
            mask_area, frame_intensities=myvid.calculate_values(myvid.frames, masks,
                                                                remove_background=params["calculate"]["remove_background"])


    dfs={}
    with pd.ExcelWriter(args.output+".xlsx") as writer:
        for key in parsed_videos.keys():
            name = key.replace(" ", "_").replace(".avi", "")
            df = pd.DataFrame(parsed_videos[key])
            dfs[name]=df
            df.to_excel(writer, sheet_name=name, index=False)

    if args.plot_results:
        os.mkdir(args.output+"_plots")
        for key in dfs.keys():



