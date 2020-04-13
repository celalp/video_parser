import numpy as np
import pandas as pd
from skimage.util import invert
from scipy import ndimage as ndi
import cv2 as cv
from skimage.exposure import adjust_log
from skimage.filters import rank
from skimage.morphology import disk
from skimage.measure import regionprops_table, label

def process_frame(frame, return_denoised=True, dsk=2, inv=False):
    """
    read a frame from opencv and pre-process for analysis
    :param frame: this is the frame returned by the video reader in opencv
    :param return_denoised: use gausian kernel denoisin
    :param dsk: size of the disk for denoising ignored if not return denoised
    :param inv: invert (for bright field images)
    :return: an array
    """

    arr=cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    adjusted=adjust_log(arr)
    if return_denoised:
        arr=rank.median(adjusted, disk(dsk))
    if inv:
        arr=invert(arr, signed_float=False)
    return arr

def generate_mask(frame, algorithm, **kwargs):
    """
    create a foreground mask using specified algorithm
    :param frame: video frame from process_frame
    :param algorithm: for foreground detection only regular KNN and MOG2 implemented
    :param kwargs: arguments for specific algorithms
    :return: a list of binary ndarrrays for foreground
    """
    if algorithm == 'MOG2':
        backSub = cv.createBackgroundSubtractorMOG2()
    elif algorithm== 'KNN':
        backSub = cv.createBackgroundSubtractorKNN()
    else:
        raise ValueError("pick and algorithm 'MOG2' or 'KNN")

    mask=backSub.apply(frame, kwargs)
    return mask

def calculate_properties(mask, image, props, to_cache, fill_holes, min_size=20000):
    """
    calculate a bunch of shape properties that are defined in config.yaml
    :param mask: mask
    :param image: frame
    :param props: a list of str, tuple of str or str
    :param to_cache: cache the results for faster computation but higher memory consumption
    :return: a data frame of single row
    """

    if fill_holes:
        mask = ndi.binary_fill_holes(mask-1)
        labels=label(mask)
    else:
        labels=label(mask)

    intensities=[]
    for lab in np.unique(labels):
        if lab == 0:
            continue
        pix_sum = np.sum(image[labels == lab])
        intensities.append(pix_sum)

    attrs=regionprops_table(label_image=labels, intensity_image=image, properties=props,
                            cache=to_cache)
    attrs=pd.DataFrame(attrs)
    attrs.insert(1, "intensities", intensities)
    attrs=attrs[attrs["area"] > min_size]

    return pd.DataFrame(attrs)
