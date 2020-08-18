import skimage.filters as filt
import pandas as pd
from utils import *
from video import Video
from multiprocessing import Pool


class Watershed:
    def threshold(self, Video=None, frames=None, method=None, cores=1, inplace=True, **kwargs):
        if method == "isodata":
            thresh_func = curry(filt.threshold_isodata, **kwargs)
        elif method == "li":
            thresh_func = curry(filt.threshold_li, **kwargs)
        elif method == "otsu":
            thresh_func = curry(filt.threshold_otsu, **kwargs)
        elif method == "yen":
            thresh_func = curry(filt.threshold_yen, **kwargs)
        elif method == "multi_otsu":
            thresh_func = curry(filt.threshold_multiotsu, **kwargs)
        else:
            raise ValueError("method can be 'isodata', 'li', "
                             "'otsu', 'multi_otsu' or 'yen")

        if frames is None and Video is not None:
            frames = Video.frames

        if cores == 1:
            markers = []
            for frame in frames:
                markers.append(thresh_func(frame))
        else:
            with Pool(cores) as p:
                markers = p.map(thresh_func, frames)

        if inplace and Video is not None:
            Video.threshold = markers
        elif inplace and Video is None:
            raise ValueError("did not specify a video class")
        else:
            return markers

    def segmentation(self, Video=None, frames=None, threshold=None, inplace=True, cores=1, **kwargs):
        if Video is not None and frames is not None:
            raise ValueError("Provided 2 sets of frames")
        elif Video is not None and frames is None:
            frames = Video.frames
        elif Video is None and frames is None:
            raise ValueError("Did not provide any frames")

        if Video is not None and threshold is not None:
            raise ValueError("Provided 2 sets of thresholds")
        elif Video is not None and threshold is None:
            threshold = Video.threshold
        elif Video is None and threshold is None:
            raise ValueError("did not provide any threshold values")

        if len(frames) != len(threshold):
            raise ValueError("your frames and markers are not the same length")
        if cores == 1:
            masks = []
            for i in range(len(frames)):
                mask = apply_watershed(frames[i], threshold[i], **kwargs)
                masks.append(mask)
        else:
            with Pool(cores) as p:
                watershed_func = curry(watershed, **kwargs)
                inputs = zip(frames, threshold)
                masks = p.starmap(watershed_func, inputs)

        if inplace and Video is not None:
            Video.masks = masks
        elif inplace and Video is None:
            raise ValueError("did not specify a video class object")
        else:
            return masks

    def properties(self, Video=None, masks=None, frames=None, cores=1, **kwargs):
        if Video is not None and frames is not None:
            raise ValueError("Provided 2 sets of frames")
        elif Video is not None and frames is None:
            frames = Video.frames
        elif Video is None and frames is None:
            raise ValueError("Did not provide any frames")

        if Video is not None and masks is not None:
            raise ValueError("Provided 2 sets of masks")
        elif Video is not None and masks is None:
            masks = Video.masks
        elif Video is None and masks is None:
            raise ValueError("did not provide any masks")

        if len(frames) != len(masks):
            raise ValueError("The number of masks and frames are not the same!")

        if cores > 1:
            with Pool(cores) as p:
                properties = curry(calculate_properties(**kwargs))
                inputs = zip(masks, frames)
                measures = p.starmap(properties, inputs)
        else:
            measures = []
            for i in range(len(masks)):
                measure = calculate_properties(masks[i], frames[i], **kwargs)
                measures.append(measure)

        measures = pd.concat(measures, ignore_index=True)
        return measures
