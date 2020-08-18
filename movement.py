import numpy as np
import cv2 as cv
from video import Video
from utils import curry
from multiprocessing import Pool

class Movement:
    def background_subtractor(self, algo, **kwargs):
        if algo == 'MOG2':
            backSub = cv.createBackgroundSubtractorMOG2(**kwargs)
        elif algo == 'KNN':
            backSub = cv.createBackgroundSubtractorKNN(**kwargs)
        elif algo == 'MOG':
            backSub = cv.bgsegm.createBackgroundSubtractorMOG(**kwargs)
        elif algo == 'GMG':
            backSub = cv.bgsegm.createBackgroundSubtractorGMG(**kwargs)
        elif algo == 'CNT':
            backSub = cv.bgsegm.createBackgroundSubtractorCNT(**kwargs)
        else:
            raise ValueError("pick and algorithm 'MOG', 'GMG', 'CNT', 'MOG2' or 'KNN")
        return backSub

    def dense_flow(self, algo, **kwargs):
        if algo == "farnebeck":
            denseFlow = cv.FarnebackOpticalFlow_create(**kwargs)
        elif algo == "dualtvl1":
            denseFlow = cv.optflow.DualTVL1OpticalFlow_create(**kwargs)
        else:
            raise ValueError("pick an algorithm 'dualtvl1' or 'farnebeck'")
        return denseFlow

    # TODO need to fix the both section and find a way to normalize
    def dense_flow_calculate(self, frame1, frame2, dense_flow, what, **kwargs):
        if frame1.shape != frame2.shape:
            raise ValueError("Your video frames are not the same shape")
        else:
            flow = dense_flow.calc(frame1, frame2, flow=None, **kwargs)
            mag, ang = cv.cartToPolar(flow[..., 0], flow[..., 1])
            if what == "magnitude":
                return mag
            elif what == "angle":
                ang = ang*180/np.pi/2
                return ang
            else:
                raise ValueError("you can get either magnitude or angle")


    def movement(self, Video, method, function, get, frames=None, inplace=True):
        if len(Video.frames) == 0 and frames is None:
            raise ValueError("you did not specify any frames")
        elif frames is None and len(Video.frames) > 0:
            frames = Video.frames
        elif frames is not None and len(Video.frames) > 0:
            raise ValueError("you specified 2 sets of frames")

        masks = []
        if method == "background":
            for frame in frames:
                mask = function.apply(frame)
                masks.append(mask)
        elif method == "optical":
            masks.append(np.zeros_like(frames[0]))
            for i in range(1, len(frames)):
                mask = self.dense_flow_calculate(frames[i - 1], frames[i], function,
                                                 what=get)
                masks.append(mask)

        else:
            raise ValueError("methods can only be 'background' or 'optical'")
        if inplace:
            Video.masks = masks
        else:
            return masks

    # this just sums up all the values, it is not meaningful for angles
    def calculate(self, Video=None, masks=None):
        if Video is not None and masks is not None:
            raise ValueError("Provided 2 sets of masks")
        elif Video is not None and masks is None:
            masks = Video.masks
        elif Video is None and masks is None:
            raise ValueError("did not provide any mask values")

        sums=[]
        for mask in masks:
            sums.append(mask.sum())

        return sums