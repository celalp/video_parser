from multiprocessing import Pool
import utils
from itertools import repeat
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as anim
from scipy import ndimage as ndi
from skimage.color import label2rgb
import pandas as pd

class Video:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError(path+" does not seem to exist")
        else:
            self.video=cv2.VideoCapture(path)
            self.frames=[]

    def get_frames(self, return_denoised=True, dsk_size=2, invert=False):
        """
        read an avi file from the class path and retrun a list of ndarrays
        :param return_denoised: use gausiian kernel denoising see utils
        :param dsk_size: disk size for denoising see utils
        :param invert: invert the image see utils
        :return: a list of ndarrays
        """
        frames = []
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
            while self.video.isOpened():
                ret, frame = self.video.read()
                if ret:
                    frames.append(utils.process_frame(frame, return_denoised,
                                                      dsk=dsk_size, inv=invert))
                else:
                    print("Done reading video ready for analysis")
                    break
            self.video.release()
        self.frames=frames

    def get_masks(self, frames, cores=1, quant=0.15):
        """
        see utils.generate_mask for details
        :param frames:
        :param cores:
        :param quant:
        :return: a list of ndarrays

        Since we are using these for pretty much everything I'm wondering whether
        these values should be part of the class
        """
        if cores > 1:
            with Pool(cores) as p:
                mask_input=zip(frames, repeat(quant, len(frames)))
                masks=p.starmap(utils.generate_mask, mask_input)
        else:
            masks = []
            for frame in frames:
                masks.append(utils.generate_mask(frame, quantile=quant))
        return masks

    def track_object(self, frames, masks, cores=1, min=10, norm=True, reference_frame=None):
        """
        There are several steps to this,
        1) get the coordinates of the mask
        2) crop the frame and the mask based on those coordinates
        3) histogram normalize
        4) match descriptors
        5) warp the frame and the mask based on matched descriptors

        if reference frame index is not specified this is done using the t-1th image
        otherwise use the reference frame number, I'm assuming this will be frame 0 in general
        """
        # GET COORDS
        coords=[]
        for mask in masks:
            coords.append(utils.calculate_coords(mask, return_mask=False))

        # CROP
        images=[]
        cmasks=[]
        for i in range(len(coords)):
            images.append(frames[i][coords[1][0]:coords[1][1], coords[1][2]:coords[1][3]])
            cmasks.append(masks[i][coords[1][0]:coords[1][1], coords[1][2]:coords[1][3]])

        # MATCH OBJECTS AND WARP
        if cores >1:
            with Pool(cores) as p:
                if reference_frame is None:
                    match_input=zip(images[:-1], images[1:], cmasks[1:],
                                    repeat(min, len(masks)-1), repeat(norm, len(masks)-1))
                else:
                    match_input = zip(repeat(images[reference_frame], len(masks)-1),
                                      images[1:], cmasks[1:],
                                      repeat(min, len(masks) - 1), repeat(norm, len(masks) - 1))
                matches=p.starmap(utils.match_objects, match_input)
                warped_frames, warped_masks = zip(*matches)
                warped_frames=list(warped_frames)
                warped_masks=list(warped_masks)
        else:
            warped_frames = []
            warped_masks = []
            for i in range(len(images)-1):
                if reference_frame is None:
                    wf,wm = utils.match_objects(images[i], images[i+1], cmasks[i+1], minmatch=min)
                else:
                    wf, wm = utils.match_objects(images[reference_frame], images[i + 1], cmasks[i + 1], minmatch=min)
                warped_frames.append(wf)
                warped_masks.append(wm)

        warped_frames.insert(0, images[0])
        warped_masks.insert(0, cmasks[0])
        return warped_frames, warped_masks

    #TODO need to be able to do this with the warped masks and frames as well.
    def calculate_values(self, frames, masks, remove_background=True):
        """
        This will subtract the warped image on frame x from original at x-1 at the
        values and return a dict of subtracted values, and mask areas
        :param warped_frames:
        :return:
        """
        if len(frames)!=len(masks):
            raise ValueError ("The number of masks and frames are not indentical!")

        mask_area=[]
        for mask in masks:
            mask_area.append(np.sum(mask))

        frame_intensities=[]
        for i in range(len(frames)):
            if remove_background:
                frame_intensities.append(np.sum(frames[i][masks[i]!=0]))
            else:
                frame_intensities.append(np.sum(frames[i]))

        return mask_area, frame_intensities

    def calculate_measures(self, masks, frames, attributes, cores=1, cached=True):
        """
        calculate a bunch of measures that are specfied in the config yaml
        :param masks:
        :param frames:
        :param attributes: which attributes to calculate see config.yaml for a complete list
        :param cores:
        :param cached: cache results for faster computation and higher memory imprint
        :return: a dataframe one row per frame and 1 or 2 columns per measure
        """
        if len(frames)!=len(masks):
            raise ValueError ("The number of masks and frames are not indentical!")

        if cores > 1:
            with Pool(cores) as p:
                measures_input=zip(masks, frames, repeat(attributes, len(masks)), repeat(cached, len(masks)))
                measures=p.starmap(utils.calculate_properties, measures_input)
        else:
            measures=[]
            for i in range(len(masks)):
                measure=utils.calculate_properties(masks[i], frames[i], props=attributes, to_cache=cached)
                measures.append(measure)

        measures=pd.concat(measures, ignore_index=True)
        return measures

    def write_mp4(self, frames, masks, outpath, what, size=(3,3), FPS=10, period=10):
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

        if len(frames)!=len(masks):
            raise ValueError ("The number of masks and frames are not indentical!")


        fig=plt.figure(figsize=size)
        ims=[]
        for i in range(len(masks)):
            if i % period ==0:
                if what=="overlay":
                    labeled_obj, _ = ndi.label(masks[i])
                    image_label_overlay = label2rgb(labeled_obj, image=frames[i])
                    ims.append([plt.imshow(image_label_overlay, animated=True)])
                elif what=="mask":
                    ims.append([plt.imshow(masks[i], animated=True)])
                elif what=="frame":
                    ims.append([plt.imshow(frames[i], animated=True)])
            else:
                continue

        ani=anim.ArtistAnimation(fig, ims, interval=int(np.round(1000/FPS)))
        filename=outpath+"/"+what+".mp4"
        ani.save(filename)
