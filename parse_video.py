import os
import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from scipy import ndimage as ndi
from skimage.color import label2rgb
import pandas as pd
import utils
from multiprocessing import Pool
from itertools import repeat

class Video:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError
        else:
            self.file=path
            self.video=cv.VideoCapture(path)

    def get_frames(self, denoised=True, dsk_size=2, invert=False):
        """
        read an avi file from the class path and retrun a list of ndarrays
        :param denoised: use gausiian kernel denoising see utils
        :param dsk_size: disk size for denoising see utils
        :param invert: invert the image see utils
        :return: a list of ndarrays
        """
        frames=[]
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
            while self.video.isOpened():
                ret, frame=self.video.read()
                if ret:
                    frames.append(utils.process_frame(frame, return_denoised=denoised,
                                  dsk=dsk_size, inv=invert))
                else:
                    print("Done reading video " + self.file)
            self.video.release()

        return frames

    #TODO normalize but may not be necessary

    def get_masks(self, frames, algo, **kwargs):
        """
        see utils generate_mask for details only KNN and MOG2 are implemented
        :param algo: algorithm for foreground detection
        :param kwargs: parameters for the algorithm
        :return: list of ndarrays
        """
        masks=[]
        for frame in frames:
            mask=utils.generate_mask(frame, algorithm=algo, **kwargs)
            masks.append(mask)

        return masks

    def calculate_measures(self, masks, frames, attributes, cores=1, cached=True, holes=True, mn_size=20000):
        """
        calculate a bunch of measures that are specfied in the config yaml
        :param masks:
        :param frames:
        :param attributes: which attributes to calculate see config.yaml for a complete list
        :param cores:
        :param cached: cache results for faster computation and higher memory imprint
        :return: a dataframe one row per frame and 1 or 2 columns per measure
        """
        if len(frames) != len(masks):
            raise ValueError("The number of masks and frames are not indentical!")

        if cores > 1:
            with Pool(cores) as p:
                measures_input = zip(masks, frames, repeat(attributes, len(masks)), repeat(cached, len(masks)),
                                     repeat(holes, len(masks)), repeat(mn_size, len(masks)))
                measures = p.starmap(utils.calculate_properties, measures_input)
        else:
            measures = []
            for i in range(len(masks)):
                measure = utils.calculate_properties(masks[i], frames[i], props=attributes, to_cache=cached,
                                                     fill_holes=holes, min_size=mn_size)
                measures.append(measure)

        measures = pd.concat(measures, ignore_index=True)
        return measures


    def write_mp4(self, frames, masks, outpath, what, size=(3, 3), FPS=10, period=10):
        """
        genereate an mp4 file for qc
        :param frames:
        :param masks:
        :param outpath: where should the file shold be written
        :param what: either frame, mask or overlay
        :param size: tuple size of the matplotlib image
        :param FPS: frames per second
        :param period: use only every nth frame
        :return: nothing
        """

        if len(frames) != len(masks):
            raise ValueError("The number of masks and frames are not indentical!")

        fig = plt.figure(figsize=size)
        ims = []
        for i in range(len(masks)):
            if i % period == 0:
                if what == "overlay":
                    labeled_obj, _ = ndi.label(masks[i] - 1)
                    image_label_overlay = label2rgb(labeled_obj, image=frames[i])
                    ims.append([plt.imshow(image_label_overlay, animated=True)])
                elif what == "mask":
                    ims.append([plt.imshow(masks[i], animated=True)])
                elif what == "frame":
                    ims.append([plt.imshow(frames[i], animated=True)])
            else:
                continue

        ani = anim.ArtistAnimation(fig, ims, interval=int(np.round(1000 / FPS)))
        filename = outpath + "/" + what + ".mp4"
        ani.save(filename)

