import skimage.exposure as exp
from functools import partial

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


#TODO bool get largest object in the selection
def calculate_properties(mask, image, props, to_cache, fill_holes, min_size=20000,
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

    attrs=regionprops_table(label_image=labels, intensity_image=image, properties=props,
                            cache=to_cache)
    attrs=pd.DataFrame(attrs)
    attrs.insert(1, "intensities", intensities)
    attrs=attrs[attrs["area"] > min_size]

    return pd.DataFrame(attrs)

