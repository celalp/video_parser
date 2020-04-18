import os
import cv2 as cv

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

    #TODO
    def optical_flower(self, algo, **kwargs):
        pass


    def movement_by_background_removal(self, subtractor, generator, invert_mask=False, **kwargs):
        if not self.video.isOpened():
            raise IOError("Error opening the video file")
        else:
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

    #TODO
    def movement_by_optical_flow(self, optical_flower, generator, **kwargs):
        pass


