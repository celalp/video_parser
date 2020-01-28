import numpy as np
import pandas as pd
from skimage.morphology import watershed, disk
from skimage.filters import scharr, threshold_multiotsu, rank
from skimage.exposure import adjust_log, match_histograms
from skimage.feature import ORB, match_descriptors
from skimage.transform import ProjectiveTransform, SimilarityTransform, warp
from skimage.measure import ransac, regionprops_table, label
from skimage.util import invert
from scipy import ndimage as ndi
import cv2


def process_frame(frame, return_denoised=True, dsk=2, inv=False):
    """
    read a frame from opencv and pre-process for analysis
    :param frame: this is the frame returned by the video reader in opencv
    :param return_denoised: use gausian kernel denoisin
    :param dsk: size of the disk for denoising ignored if not return denoised
    :param inv: invert (for bright field images)
    :return: an array
    """
    arr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    adjusted = adjust_log(arr)
    if return_denoised:
        arr = rank.median(adjusted, disk(dsk))
    if inv:
        arr=invert(arr, signed_float=False)
    return arr

def generate_mask(frame, levels=4):
    """
    generate a mask using otsu's method
    :param frame: frame to detect a single object in
    :param levels: the number of bins for the multiotsu threshold if there are overexposed regions use 4 otherwise 3 is good
    :return: the mask as an nd array
    """
    tresholds=threshold_multiotsu(frame, levels)
    markers = np.zeros_like(frame)
    markers[frame < tresholds[0]] = 1
    markers[frame > tresholds[1]] = 2
    elevation = scharr(frame)
    segmentation = watershed(elevation, markers)
    segmentation=segmentation.astype(np.uint8)
    return segmentation

def calculate_coords(mask, return_mask=True):
    """
    calculate the coordinates (bounding box of the mask or return a boolean ndarray for mask
    :param mask: mask ndarray
    :param return_mask: return a boolean array for the bounding box instead of the coordinates
    :return:
    """
    y_coords = []
    x_coords = []
    y_range = mask.sum(axis=0)
    x_range = mask.sum(axis=1)
    for i in range(len(x_range)):
        if x_range[i] == 0:
            continue
        else:
            x_coords.append(i)

    for i in range(len(y_range)):
        if y_range[i] == 0:
            continue
        else:
            y_coords.append(i)
    coords=(min(x_coords), max(x_coords), min(y_coords), max(y_coords))

    if return_mask:
        rect_mask=np.zeros_like(mask, dtype=np.uint8)
        rect_mask[coords[0]:coords[1], coords[2]:coords[3]]=1
        rect_mask=rect_mask.astype(bool)
        return rect_mask
    else:
        return coords

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

def normalize_pics(image1, image2):
    """
    normalize histogram of image2 compared to image1
    :param image1:
    :param image2:
    :return: new normalized image
    """
    normalized=match_histograms(image2, image1, multichannel=False)
    return(normalized)

def crop(array, coords):
    """
    crop an image based on the coordinates usually the bounding box of the mask
    :param array: image
    :param coords: box
    :return:
    """
    cropped = array[coords[1][0]:coords[1][1], coords[1][2]:coords[1][3]]
    return cropped


def match_objects(image1, image2, mask2, minmatch=10, normalize=True):
    """
    use the ORB algorithm to detect interesting features and warp image2 and it's mask based on the features matched
    :param image1:
    :param image2:
    :param mask2:
    :param minmatch: minimum # of interesting features
    :param normalize: normalize histograms (see above)
    :return: warped image and mask as ndarrays
    """

    if normalize:
        image2=normalize_pics(image1, image2)


    orb1=ORB(n_keypoints=100, fast_threshold=0.05)
    orb1.detect_and_extract(image1)
    orb2 = ORB(n_keypoints=100, fast_threshold=0.05)
    orb2.detect_and_extract(image2)

    matches = match_descriptors(orb1.descriptors, orb2.descriptors, cross_check=True)
    src = orb1.keypoints[matches[:, 0]][:, ::-1]
    dst = orb2.keypoints[matches[:, 1]][:, ::-1]

    model_robust, inliers = ransac((src, dst), ProjectiveTransform,
                                    min_samples=minmatch, residual_threshold=1,
                                    max_trials=100)
    r, c = image2.shape[:2]
    corners = np.array([[0, 0],
                        [0, r],
                        [c, 0],
                        [c, r]])

    warped_corners = model_robust(corners)
    all_corners = np.vstack((warped_corners, corners))

    corner_min = np.min(all_corners, axis=0)
    corner_max = np.max(all_corners, axis=0)
    output_shape = (corner_max - corner_min)

    output_shape = np.ceil(output_shape[::-1]).astype(int)
    offset = SimilarityTransform(translation=-corner_min)

    image2_warped = warp(image2, offset.inverse, order=3,
                        output_shape=output_shape, cval=0)

    mask2_warped=warp(mask2, offset.inverse, order=3,
                        output_shape=output_shape, cval=0)

    return image2_warped, mask2_warped