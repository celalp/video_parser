import os
import cv2 as cv
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import numpy as np


class Video:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError
        else:
            self.file=path
            self.video=cv.VideoCapture(path)

    def frame_generator(self, invert=False):
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
            while self.video.isOpened():
                ret, frame =self.video.read()
                if frame is None:
                    print("Done reading video " + self.file)
                    break
                else:
                    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                    if invert:
                        frame=cv.bitwise_not(frame)
                    yield frame

    def subtractor(self, algo, **kwargs):
        if algo == 'MOG2':
            backSub = cv.createBackgroundSubtractorMOG2(**kwargs)
        elif algo == 'KNN':
            backSub = cv.createBackgroundSubtractorKNN(**kwargs)
        else:
            raise ValueError("pick and algorithm 'MOG2' or 'KNN")
        return backSub

    def movement_by_background_removal(self, subtractor, generator, invert_mask=False, **kwargs):
        frames=[]
        masks=[]

        for frame in generator:
            frames.append(frame)
            mask=subtractor.apply(frame, **kwargs)
            if invert_mask:
                mask=cv.bitwise_not(mask)
            masks.append(mask)
        #skipping the first one because that is a blank mask
        return frames[1:], masks[1:]

    #TODO this seems simple concat frames and masks and write to path
    def write_mp4(self, frames, masks, output, size=(3,3), FPS=10, period=30):
        if len(frames) != len(masks):
            raise ValueError("the number frames do not match number of masks")
        else:
            fig = plt.figure(figsize=size)
            ims=[]
            for i in range(len(frames)):
                if i % period==0:
                    combined=cv.hconcat([frames[i], masks[i]])
                    ims.append([plt.imshow(combined, animated=True)])
                else:
                    continue

            ani=anim.ArtistAnimation(fig, ims, interval=int(np.round(1000/FPS)))
            ani.save(output)








