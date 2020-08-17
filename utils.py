import skimage.exposure as exp
from functools import partial
from skimage.segmentation import watershed
import numpy as np




def adjust(frame, method, **kwargs):
    if method=="equalize":
        adjusted=exp.equalize_hist(frame, **kwargs)
    elif method=="gamma":
        adjusted=exp.adjust_gamma(frame **kwargs)
    elif method=="log":
        adjusted=exp.adjust_log(frame, **kwargs)
    elif method=="sigmoid":
        adjusted=exp.adjust_sigmoid(frame, **kwargs)
    elif method=="adaptive":
        adjusted=exp.equalize_adapthist(frame, **kwargs)
    else:
        raise ValueError("method can be equalize, gamma, log, sigmoid or adaptive")
    return adjusted



def curry(orig_func, **kwargs):
    newfunc=partial(orig_func, **kwargs)
    return newfunc

def apply_watershed(frame, threshold, **kwargs):
    markers=np.zeros_like(frame)
    if type(threshold)==np.ndarray:
        markers[frame < threshold[0]] = 1
        markers[frame > threshold[len(threshold) - 2]] = 2
    else:
        markers[frame < threshold] = 1
        markers[frame > threshold] = 2

    mask=watershed(frame, markers, **kwargs)
    return mask

def calculate_properties(mask, image, props=None, to_cache=True, fill_holes=False, min_size=20000,
                         get_largest=False):
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

    if props is None:
        props=["label", "area", "bbox_area", "convex_area", "eccentricity", "extent", "local_centroid",
               "major_axis_length", "minor_axis_length", "perimeter", "solidity",
               "weigthed_local_centroid", "orientation"]
    else:
        props.insert(0, "label")

    attrs = pd.DataFrame(attrs)
    attrs.insert(1, "intensities", intensities)

    if not get_largest:
        attrs=attrs[attrs["area"] > min_size]
    else:
        attrs=attrs[attrs["area"]==attrs["area"].max()]

    return pd.DataFrame(attrs)


