
# Reading Video files



# adjustment

### gamma

Transform the image pixel wise according to the equation I\*\*gamma after scaling each pixel to range 0 to 1

+ gamma: 1 non negative real number
+ gain: 1, constant multiplier

### equalize

Histogram equalization

+ nbins: 256, number of bins - for an 8 bit image 256 is reccomended
+ mask: None, ndarray of bools or 0s and 1s to specify which region of the image to apply equalization

### log

Logarighmic correction on the input image based on gain\*log(1+I) after scaling each pixel to range 0 to 1. 

+ gain: 1, constant multiplier
+ inv: False, inverse log correction gain\*(2\*\*I)-1)

### sigmoid

Sigmoid correction (also known as contrast adjustment) 1/(1+exp\*(gain\*(cutoff-I))), after scaling each pixel to range 0 to 1

+ cutoff: 0.5, direction of the curve shift
+ gain: 10, constant multiplier
+ inv: False, negative sigmoid correction

### adaptive

Contrast Limited Adaptive Histogram Equalization, for local contrast enhancement that uses histograms over different tile regions. This way local densities can be enhanced even in darker or lighter regions. 

+ kernel_size: None, int or array defining the tile size for local histograms, default is 1/8th of the image height and width
+ clip_limit: 0.01, between 0 and 1 higher values give greater contrast
+ nbins: 256, number of bins for an 8 bit image 256 is reccomended. 


# object detection

`Object` Class

This class has multiple methods. See below for most common parameters for each of these. A more detailed explanation can be found on scikit-image website

To start you can initate an empty object class:

```python
from object import Object
obj_detection=Object()
```

After that you need to 

1. calculate markers using an algorithm of your choice
2. segment the image using the watershed algorithm and create it's mask
3. calculate different properties of the mask

You can create markers and masks in place, meaning they will be saved inside the `Video` object or you can choose to return them as a list of ndarrays. The latter is useful for trying multiple algorithms. 

```python
obj_detection.markers(myvid, "otsu")
obj_detection.watershed(myvid)
obj_detection.properties(myvid)
```

## markers

### isodata

Calculate threshold based on ISODATA method, also known as Ridler-Calvard method or inter-means. The lowest value that satisfies the equality 

```threshold=(image[image <=threshold]).mean()+image[image > threshold].mean())/2```

Separating the image into 2 groups of pixels where the intensity is midway between these groups. 

+ nbins: 256, number of bins 256 is the reccomended value of 8 bit images. 

### li

Compute Li's iterative Minimum Cross Entropthy method

+ tolerance: None, finish computation when the change in threshold in an iteration is less than this value, the default is 1/2 smallest difference between intesity values. 

### otsu

Return a threshold value based on Otsu's method. 

+ nbins: 256, number of bins this is the reccomended value for 8 bit images

### multi_otsu

generate classes-1 threshold values to divide the image using otsu's method. 

+ classes: 3, integer
+ nbins: 256, number of bins this is the reccomended value for 8 bit images

### yen

Return threshold value based on Yen’s method.

+ nbins: 256, number of bins this is the reccomended value for 8 bit images


## compact watershed algorithm

+ markers: the output of markers method in the object class
+ connectivity: None, ndarray whose dimensions are the same as the image and non-zero elements indicate neighbors for connection
+ offset: None, array_like-offset of the connectivity
+ mask: None, array_like same shape as image 
+ compactness: 0, float-larger values result in more regularly shaped basisns
+ watershed_line: False, whether to draw the watershed lines as a sinlge pixel wide line. Turning this on might negatively effect labelling downstream

## calculated properties

By default all of these measures are calculated. 

+ sum_intensities: sum of the pixel intensities in the masked area
+ area: mask area
+ bbox_area: area of the bounding box
+ convex_area: area of the convex hull
+ eccentricity: how eliptical is the mask
+ extent: area of bounding box/area of mask
+ local_centroid: centre of mass of the mask
+ major_axis_length: of the bounding ellipse
+ minor_axis_length: of the bounding ellipse
+ perimeter: of the mask
+ solidity: how rectangular is the mask
+ weighted_local_centroid: centre of mass of the mask

# motion detection

## background subtraction

Most of these background subtraction methods have a detect shadows option, however using this option is not reccomended unless you are actually trying to detect the shadows of your object. 

Each models also has it's own getters and setters that are documented in opencv documentation. If desired more advanced users can set these parameters using the object attribute setters. 

The background_subtractor and dense_flow methods return classes of their respective algoritms. We can then use these classes and all the methods that come with them in our calculations. 

### MOG2

Use Mog2 Background Subtractor

+ history:500,int length of the history
+ varThreshold:16, int threshold of the squared sitance between the pixel and the model to decide whether a pixel is well described by the model. Higher values reduce sensitivity. 

### KNN

Use K-nearest neightbor model to 

+ history: int, lenght of history
+ dist2Threshold: Threshold 

### MOG

Creates non-adaptive mixture-of-gaussian background subtractor. 

+ history:200, int length of history
+ nmixture: 5, int number of gaussian mixtures to use
+ backgroundRatio: 0.7, fraction of the image that is background
+ noiseSigma: 0, noise strength (standard deviation of the brightness) 0 means an automatic value

### GMG

GMG background Subtractor

+ initializationFrames=120, int number of frames to used to initialize background model
+ desicionThreshold=0.8, the treshold to mark foreground/background

### CNT

Count based background subtractor

+ minPixelStability: 15, int number of frames with the same pixel color to consider stable
+ useHistory: True, whether to give pixel credit for being stable for a long time
+ maxPixelStability: maximum credit for stability
+ isParallel: True, whether to parallelize


## dense optical flow

These are the dense optical flow methods implemented. Like the background subtraction methods they have some parameters that are easy to set during initialization. These are presented here. Other parameters can be set using the attribute setters that are documented in opencv. 

### farneback

Class computing a dense optical flow using the Gunnar Farneback's algorithm.

+ numLevels:5 says, there are no extra layers (only the initial image) . It is the number of pyramid layers including the first image.
+ pyrScale: 0.5 parameter specifying the image scale to build pyramids for each image (scale < 1). A classic pyramid is of generally 0.5 scale, every new layer added, it is halved to the previous one
+ fastPyramids: False
+ winSize: 13  It is the average window size, larger the size, the more robust the algorithm is to noise, and provide fast motion detection, though gives blurred motion fields.
+ numIters: 10
+ polyN: 5 it is typically 5 or 7, it is the size of the pixel neighbourhood which is used to find polynomial expansion between the pixels.
+ polySigma: 1.1 standard deviation of the gaussian that is for derivatives to be smooth as the basis of the polynomial expansion. It can be 1.1 for poly= 5 and 1.5 for poly= 7.


### dualtvl1

Dual TV L1" Optical Flow

+ tau:0.25, time step of the numerical scheme
+ lambda:0.15, determines the smoothness of the output, the smaller the parameter the smoother the solution
+ theta: 0.3, tightness parameter
+ nscales: 5, number of scales to create pyramid of images
+ warps: 5, number of warpings per scale, larger values will create more accurate but slower results
+ epsilon: 0.01, stopping criterion threshold-the tradeoff between precision and runtime. Smaller values will give more accurate results but will be slower. 