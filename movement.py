import numpy as np
import cv2 as cv
from video import Video

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
    def dense_flow_calculate(self, frame1, frame2, dense_flow, get, **kwargs):
        if frame1.shape != frame2.shape:
            raise ValueError("Your video frames are not the same shape")
        else:
            hsv = np.zeros((frame1.shape[0], frame1.shape[1], 3))
            flow = dense_flow.calc(frame1, frame2, flow=None, **kwargs)
            mag, ang = cv.cartToPolar(flow[..., 0], flow[..., 1])
            if get == "magnitude":
                return mag
            elif get == "angle":
                return ang
            elif get == "both":
                hsv[..., 0] = ang * 180 / np.pi / 2
                hsv[..., 1] = 255
                hsv[..., 2] = mag
                rgb = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
                return rgb

    def calculate(self, Video, method, function, what, inplace=True, **kwargs):
        masks = []
        if method == "background":
            for frame in Video.frames:
                mask = function.apply(frame, **kwargs)
                masks.append(mask)
        elif method == "optical":
            for i in range(1, len(Video.frames)):
                mask = self.dense_flow_calculate(Video.frames[i - 1], Video.frames[i], function,
                                                 get=what, **kwargs)
                masks.append(mask)
        else:
            raise ValueError("methods can only be 'background' or 'optical'")
        if inplace:
            Video.masks=masks
        else:
            return masks
