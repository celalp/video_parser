import os
import cv2 as cv
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import numpy as np
from skimage.filters import rank
from skimage.morphology import disk
from utils import *

#TODO mignt need to add scikit-image here

class Video:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError
        else:
            self.file=path
            self.video=cv.VideoCapture(path)
            self.frames=[]

    def get_frames(self, invert=False, denoise=False, dsk=None):
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
            while self.video.isOpened():
                ret, frame =self.video.read()
                if frame is None:
                    print("Done reading video " + self.file)
                    self.video.release()
                    break
                else:
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                    if invert:
                        frame=cv.bitwise_not(frame)
                    if denoise:
                        if disk is None:
                            print("Using default disk value 2")
                            dsk=2
                        frame=rank.median(frame, disk(dsk))
                    self.frames.append(frame)
            print("Done reading frames for " + self.file)

    def match_histograms(self, reference_frame=0):
        if reference_frame is None:
            print("No reference frame provided using the first frame as reference")
            reference_frame=0


    def write_mp4(self, output, size=(3, 3), FPS=10, period=30):
        if len(self.frames) != len(self.maskss):
            raise ValueError("the number frames do not match number of masks")
        else:
            fig = plt.figure(figsize=size)
            ims = []
            for i in range(len(self.frames)):
                if i % period == 0:
                    combined = cv.hconcat([self.frames[i], self.masks[i]])
                    ims.append([plt.imshow(combined, animated=True)])
                else:
                    continue

            ani = anim.ArtistAnimation(fig, ims, interval=int(np.round(1000 / FPS)))
            ani.save(output)