import os
import cv2 as cv
import matplotlib.animation as anim
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import numpy as np
from skimage.filters import rank
from skimage.morphology import disk
from skimage.exposure import match_histograms
import utils


class Video:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError
        else:
            self.file = path
            self.video = cv.VideoCapture(path)
            self.frames = []
            self.threshold = None
            self.masks = []

    def get_frames(self, invert=False, denoise=False, dsk=None):
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
            while self.video.isOpened():
                ret, frame = self.video.read()
                if frame is None:
                    print("Done reading video " + self.file)
                    self.video.release()
                    break
                else:
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                    if invert:
                        frame = cv.bitwise_not(frame)
                    if denoise:
                        if disk is None:
                            print("Using default disk value 2")
                            dsk = 2
                        frame = rank.median(frame, disk(dsk))
                    self.frames.append(frame)
            print("Done reading frames for " + self.file)

    def normalize_frames(self, inplace=True, reference_frame=0):
        if reference_frame is None:
            print("No reference frame provided using the first frame as reference")
            reference_frame = 0
        adjusted_frames = []
        for i in range(len(self.frames)):
            if i == reference_frame:
                continue
            else:
                matched = match_histograms(self.frames[i], self.frames[reference_frame], multichannel=False)
                adjusted_frames.append(matched)
        if inplace:
            self.frames = adjusted_frames
        else:
            return adjusted_frames

    def adjust(self, inplace=True, **kwargs):
        adjusted = []
        for frame in self.frames:
            adjusted.append(utils.adjust(frame, **kwargs))
        if inplace:
            self.frames = adjusted
        else:
            return adjusted

    def write_mp4(self, output, frames=None, masks=None, size=(6, 3), FPS=10, period=30, normalize=False):
        if len(self.frames) == 0 and frames is None:
            raise ValueError("you did not specify any frames")
        elif frames is None and len(self.frames) > 0:
            frames = self.frames
        elif frames is not None and len(self.frames) > 0:
            raise ValueError("you specified 2 sets of frames")

        if len(self.masks) == 0 and masks is None:
            raise ValueError("you did not specify any masks")
        elif masks is None and len(self.masks) > 0:
            masks = self.masks

        if len(frames) != len(masks):
            raise ValueError("the number frames do not match number of masks")
        else:
            fig, (ax1, ax2) = plt.subplots(1,2)
            fig.set_size_inches(size)
            ims=[]
            if normalize:
                stacked = np.stack(masks, axis=2)
                max_val = stacked.max()
                min_val = stacked.min()
            for i in range(len(frames)):
                if i % period == 0:
                    im1 = ax1.imshow(frames[0], animated=True)
                    if normalize:
                        im2 = ax2.imshow(masks[i], animated=True, norm=Normalize(min_val, max_val))
                    else:
                        im2 = ax2.imshow(masks[i], animated=True)
                    ims.append([im1, im2])
                else:
                    continue
            ani = anim.ArtistAnimation(fig, ims, interval=int(np.round(1000 / FPS)))
            ani.save(output)
