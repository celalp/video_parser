import numpy as np
import cv2 as cv


class Movement:
    def background_subtractor(self, algo, **kwargs):
        if algo == 'MOG2':
            backSub = cv.createBackgroundSubtractorMOG2(**kwargs)
        elif algo == 'KNN':
            backSub = cv.createBackgroundSubtractorKNN(**kwargs)
        elif algo=='MOG':
            backSub=cv.bgsegm_BackgroundSubtractorMOG(**kwargs)
        elif algo=='LSBP':
            backSub=cv.bgsegm_BackgroundSubtractorLSBP(**kwargs)
        elif algo=='GSOC':
            backSub = cv.bgsegm_BackgroundSubtractorGSOC(**kwargs)
        elif algo=='GMG':
            backSub = cv.bgsegm_BackgroundSubtractorGMG(**kwargs)
        elif algo=='CNT':
            backSub = cv.bgsegm_BackgroundSubtractorCNT(**kwargs)
        else:
            raise ValueError("pick and algorithm 'MOG', 'LSBP', 'GSOC', 'GMG', 'CNT', 'MOG2' or 'KNN")
        return backSub

    def dense_flow(self, algo, **kwargs):
        if algo=="dis":
            denseFlow=cv.DISOpticalFlow_create(**kwargs)
        elif algo=="farneback":
            denseFlow=cv.FarnebackOpticalFlow_create(**kwargs)
        elif algo=="rlof":
            denseFlow=cv.optflow.DenseRLOFOpticalFlow_create(**kwargs)
        elif algo=="dualtvl1":
            denseFlow=cv.optflow.DualTVL1OpticalFlow_create(**kwargs)
        else:
            raise ValueError("pick an algorithm 'dualtvl1', 'farnabeck',  'dis', 'rlof'")
        return denseFlow


    #TODO both of these will need some features so will both use shi-thomasi need to create the
    # points to the calucluate function
    def sparse_flow(self, algo, **kwargs):
        if algo=="rlof":
            sparseFlow=cv.optflow.SparseRLOFOpticalFlow_create(**kwargs)
        elif algo=="pyrlko":
            sparseFlow=cv.SparsePyrLKOpticalFlow_create(**kwargs)
        else:
            raise ValueError("pick an algorithm 'rlof' or 'pyrlko'")

        return sparseFlow

    def dense_flow_calculate(self, frame1, frame2, dense_flow, **kwargs):
        if frame1.shape !=frame2.shape:
            raise ValueError("Your video frames are not the same shape")
        else:
            hsv = np.zeros((frame1.shape[0], frame1.shape[1], 3))
            flow = dense_flow(frame1, frame2, **kwargs)
            mag, ang = cv.cartToPolar(flow[..., 0], flow[..., 1])
            hsv[..., 1] = 255
            hsv[..., 0] = ang * 180 / np.pi / 2
            #TODO need to come up with a way to globally normalize magnitudes
            hsv[..., 2] = cv.normalize(mag, None, 0, 255, cv.NORM_MINMAX)
            bgr = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
            return bgr

    def sparse_flow_calculate(self, features, **kwargs):
        pass

    #TODO this will be used to calculate and will be applied to Video.frames and will write to Video.masks
    def calculate(self, Video, method,  **kwargs):
        if method[0]=="background detect":
            pass
        elif method[0]=="dense":
            pass
        elif method[0]=="sparse":
            pass
        else:
            raise ValueError