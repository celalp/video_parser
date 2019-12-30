import numpy as np
from skimage.morphology import watershed, disk
from skimage.filters import scharr, threshold_otsu, rank
from skimage.exposure import adjust_log, match_histograms
from skimage.feature import ORB, match_descriptors
from skimage.transform import ProjectiveTransform, SimilarityTransform, warp
from skimage.measure import ransac
from skimage.util import invert
from scipy import ndimage as ndi
import cv2


def process_frame(frame, return_denoised=True, dsk=2, inv=False):
    arr = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    adjusted = adjust_log(arr)
    if return_denoised:
        arr = rank.median(adjusted, disk(dsk))
    if inv:
        arr=invert(arr, signed_float=False)
    return arr

def generate_mask(frame, quantile=0.15):
    markers = np.zeros_like(frame)
    markers[frame < np.quantile(frame, quantile)] = 1
    markers[frame > threshold_otsu(frame)] = 2
    elevation = scharr(frame)
    segmentation = watershed(elevation, markers)
    segmentation = ndi.binary_fill_holes(segmentation - 1)
    segmentation=segmentation.astype(np.uint8)
    return segmentation

def calculate_coords(mask, return_mask=True):
    """
    the centre of mass is the centre of mass of the mask the pixel values are not counted
    :param mask: mask from get_masks
    :return: a tuple of tuples, first the coords of a rectangle second the center of the
    the rectangle
    third the centre of mass
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

def normalize_pics(image1, image2):
    normalized=match_histograms(image2, image1, multichannel=False)
    return(normalized)

def crop(array, coords):
    cropped = array[coords[1][0]:coords[1][1], coords[1][2]:coords[1][3]]
    return cropped


def match_objects(image1, image2, mask2, minmatch=10, normalize=True):

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