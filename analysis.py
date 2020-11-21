import yaml
import pandas as pd
import argparse as arg
import video as vid
import os
from datetime import datetime
import shutil
import object as obj
import movement as mov

if __name__ == "__main__":
    parser = arg.ArgumentParser(description='detect objects or movements in a video file')
    parser.add_argument('-f', '--filename', type=str, help='avi file', action="store", default=None)
    parser.add_argument('-d', '--directory', type=str, help="directory of avi files and nothing else", default=None)
    parser.add_argument('-y', '--config_yaml', type=str, help='path of the config.yaml file', action="store")
    parser.add_argument('-e', '--extension', type=str, help='file extension default .avi', action="store",
                        default=".avi")
    parser.add_argument('-o', '--output', type=str, help='name of the output directory, this will have subdirectories',
                        action="store")
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
            else:
                continue

    parsed_videos = {}
    for file in files:
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Parsing frames for " + file)
        myvid = vid.Video(path=file)
        if "denoise" in params["video"].keys():
            denoise = True
            if "disk" not in params["video"]["denoise"].keys():
                disk = 2
            else:
                disk = params["video"]["denoise"]["disk"]
        else:
            denoise = False
            disk = None

        if params["video"]["invert"]:
            invert = True
        else:
            invert = False

        myvid.get_frames(invert=invert, denoise=denoise, dsk=disk)

        if "adjust" in params["video"].keys():
            if "method" not in params["video"]["method"]:
                raise ValueError("You did not specify an adjustment algorithm")
            else:
                myvid.adjust(method=params["video"]["adjust"] **params["adjust"]["method_params"])

        if "normalize" in params["video"]:
            if "reference_frame" in params["video"]["normalize"]:
                reference_frame = params["video"]["normalize"]
            else:
                reference_frame = None
            myvid.normalize_frames(reference_frame=reference_frame)

        if "cores" in params.keys():
            cores = params["cores"]
        else:
            cores = 1

        if params["method"] == "object_detection":
            if "algorithm" not in params["threshold"].keys():
                raise ValueError("You did not specify a tresholding algorithm")
            else:
                seg = obj.Watershed()
                print("[" + datetime.now().strftime(
                    "%Y/%m/%d %H:%M:%S") + "] " + "Calculating thresholding valules " + file)
                seg.threshold(Video=myvid, method=params["threshold"]["algorithm"], cores=cores,
                              **params["threshold"]["algorithm"]["algorithm_params"])
                print("[" + datetime.now().strftime(
                    "%Y/%m/%d %H:%M:%S") + "] " + "Performing watershed segmentation " + file)
                seg.segmentation(Video=myvid, cores=cores, **params["segmentation_params"])
                print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Calculating properties " + file)
                if "calculate" not in params.keys():
                    print("Using default values for property calculations see readme for details")
                    results = seg.properties(Video=myvid, cores=cores)
                else:
                    results = seg.properties(Video=myvid, cores=cores, **params["calculate"])

        elif params["method"] == "movement_detection":
            movement = mov.Movement()
            if "type" not in params.keys():
                raise ValueError(
                    "You did not specify a calculation type, it's either background_subtraction or optical_flow")
            elif "algorithm" not in params.keys():
                raise ValueError("You did not specify an algorithm to use see readme for details")
            else:
                if params["type"] == "background_subtraction":
                    print("[" + datetime.now().strftime(
                        "%Y/%m/%d %H:%M:%S") + "] " + "Performing background subtraction " + file)
                    back_sub = movement.background_subtractor(algo=params["algorithm"]["name"],
                                                              **params["algorithm"]["algo_params"])
                    movement.movement(myvid, method="background", function=back_sub)
                    zippedList = list(zip(range(len(myvid.masks)), [mask.sum() for mask in myvid.masks]))
                    results = pd.DataFrame(zippedList, columns=['frame', 'movement'])

                elif params["type"] == "optical_flow":
                    print("[" + datetime.now().strftime(
                        "%Y/%m/%d %H:%M:%S") + "] " + "Performing dense optical flow " + file)
                    dense=movement.dense_flow(params["algorithm"]["name"], **params["algorithm"]["algo_params"])
                    movement.movement(myvid, method="optical", function=dense, get=params["algorithm"]["return"])
                    if params["algorithm"]["return"]=="magnitude":
                        zippedList = list(zip(range(len(myvid.masks)), [mask.sum() for mask in myvid.masks]))
                        results = pd.DataFrame(zippedList, columns=['frame', 'total_movement'])
                    else:
                        zippedList = list(zip(range(len(myvid.masks)), [mask.sum() for mask in myvid.masks]))
                        results = pd.DataFrame(zippedList, columns=['frame', 'aggregate_angle'])
                else:
                    raise ValueError("type can only be background_subtraction or optical_flow")

        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Preparing results for " + file)
        filename=file.split("/").pop()
        filename=filename.replace(args.extension, "")
        print(filename)
        resultsdir = os.path.abspath(args.output) + "/" + filename
        os.makedirs(resultsdir, exist_ok=True)
        with pd.ExcelWriter(resultsdir + "/results.xlsx") as writer:
            results.to_excel(writer, sheet_name="properties", index=False)

        if "output" in params.keys():
            if "video" in params["output"]:
                vidname = resultsdir + "/results.mp4"
                print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Generating mp4 for " + file)
                if "size" not in params["video"].keys():
                    size = (6, 3)
                else:  # this will give a key error is the user messes up so I'm going to leave it
                    size = (params["video"]["size"]["width"], params["video_ouptut"]["size"]["height"])

                if "FPS" not in params["video"].keys():
                    FPS = 10
                else:
                    FPS = params["video"]["FPS"]

                if "periodicity" not in params["video"].keys():
                    period = 30
                else:
                    period = params["video"]["periodicity"]

                myvid.write_mp4(output=vidname, size=size, FPS=FPS, period=period)
                print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + "Done analyzing " + file)
            if "raw" in params["output"]:
                rawname=resultsdir+"/raw_data.hdf5"
                myvid.write_raw(rawname)

        shutil.copy(args.config_yaml, resultsdir + "/config.yaml")
        print("[" + datetime.now().strftime("%Y/%m/%d %H:%M:%S") + "] " + file + " done!")
