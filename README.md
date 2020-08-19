# Parse gut slice videos

This is the mini python package I used to analyse the gut slice videos. Two different kinds of analyses methods
are implemented. Object detection is for detecting single object in the video and tracking different attibutes 
throughout. Movement detection does not concern itself with objects and only keeps track of how much movement
there is. 

# Installation

This package was written in python 3.7 so that needs to be installed. See [python documentation](https://www.python.org/) 
for OS specific installation instructions. After python and git installation you can simply clone this repository using:

```bash
git clone https://github.com/celalp/video_parser
```

## Dependencies

This package has several dependencies, they are in the `requriements.txt` package. After python installation those can be 
installed using `pip`. If `pip` is not installed in your system you can use [these instructions](https://pip.pypa.io/en/stable/installing/) 
to install `pip` and run the command: 

```bash
pip install -r requriements.txt
```

Keep in mind that if you have multiple versions of python installed (python2 vs 3 or python 3.5 vs 3.6) you might want to 
follow [different instructions](https://stackoverflow.com/questions/2812520/dealing-with-multiple-python-versions-and-pip).

# Built in classes

There are 3 built in classes in this package along with some helper funcitons in the `utils.py` file. Their descriptions
and default parameters are below:

## Video

This class stores all the relevant information about the video in question and has several methods that you can use to
get individual frames, perform histogram, exposure, contrast adjustments and write analysis results. To start you can 
initiate a `Video` class with the path to your file. 

```python
from video import Video
myvid=Video(path="path/to/myfile.avi")
```

We can then parse the data using [opencv](https://opencv.org/). At its backend in additon to opencv this package
uses ffmpeg to read the video files. To parse the video frames into individual `ndarrays` you can do:

```python
myvid.get_frames(invert=False, denoise=False, dsk=None)
``` 

`invert` simple inverst the image. If you have a bright background and dark object this might be useful. Denoising
is done by simple gaussian blur. The disk `dsk` size determines the extent of the blur. This could be useful if you have 
a lot of grainy underexposed images. After reading the video into memory you can perform several adjustments using

```python
myvid.adjust(inplace=False, **kwargs)
``` 
If you choose inplace the current `Video.frames` attribute will be overwritten, otherwise the method will return a list
of ndarrays with the proper adjustment. The available adjustments and their keywords are:

### gamma

Transform the image pixel wise according to the equation I*gamma after scaling each pixel to range 0 to 1

+ gamma: 1 non negative real number
+ gain: 1, constant multiplier

### equalize

Histogram equalization

+ nbins: 256, number of bins - for an 8 bit image 256 is recommended
+ mask: None, ndarray of bools or 0s and 1s to specify which region of the image to apply equalization

### log

Logarighmic correction on the input image based on gain*log(1+I) after scaling each pixel to range 0 to 1. 

+ gain: 1, constant multiplier
+ inv: False, inverse log correction gain*(2**I)-1)

### sigmoid

Sigmoid correction (also known as contrast adjustment) 1/(1+exp*(gain*(cutoff-I))), after scaling each pixel to range 0 to 1

+ cutoff: 0.5, direction of the curve shift
+ gain: 10, constant multiplier
+ inv: False, negative sigmoid correction

### adaptive

Contrast Limited Adaptive Histogram Equalization, for local contrast enhancement that uses histograms over different tile regions. This way local densities can be enhanced even in darker or lighter regions. 

+ kernel_size: None, int or array defining the tile size for local histograms, default is 1/8th of the image height and width
+ clip_limit: 0.01, between 0 and 1 higher values give greater contrast
+ nbins: 256, number of bins for an 8 bit image 256 is recommended. 

If you have some under some overexposed images you can match their histograms to a reference frame using:

```python
myvid.normalize_frames(inplace=False, reference_frame=None)
```

If no reference frame is provided the first one will be used with a message. 

After performing your analysis you can generate an mp4 file with your video and/or you can write the processed frames
and masks into an `hdf5` file. 

The hdf5 file ony records the frames and the masks generated as a stacked `ndarray` that has the dimensions 
(image width, image height, number of frames)

```python
# this will generate an mp4 file using every 30th frame. Normalization is only meaningful for 
# optical flow since the magnitude of the movement is calculated for each frame individually
myvid.write_mp4("results.mp4", size=(6,3), FPS=10, period=30, normalize=False)

myvid.write_raw("results.hdf5")
```
After reading the video frames into memory you can start analyzing your videos. 

## Movement

The movement class is responsible for handling optical flow and background subtraction methods. The current implemented
methods are from opencv. 

### Background subtraction:

Most of these background subtraction methods have a detect shadows option, however using this option is not 
recommended unless you are actually trying to detect the shadows of your object. Each models also has it's 
own getters and setters that are documented in opencv documentation. If desired more advanced users can set 
these parameters using the object attribute setters. The background_subtractor return classes of their 
respective algoritms. We can then use these classes and all the methods and properties 
that come with them in our calculations. 

Supported background subtraction methods and their default values are:

#### MOG2

Use Mog2 Background Subtractor

+ history:500,int length of the history
+ varThreshold:16, int threshold of the squared sitance between the pixel and the model to decide whether a pixel is well described by the model. Higher values reduce sensitivity. 

#### KNN

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
+ desicionThreshold=0.8, the threshold to mark foreground/background

### CNT

Count based background subtractor

+ minPixelStability: 15, int number of frames with the same pixel color to consider stable
+ useHistory: True, whether to give pixel credit for being stable for a long time
+ maxPixelStability: maximum credit for stability
+ isParallel: True, whether to parallelize

To create a background subtractor one would need to load the module and intiaite a movement class. 

```python
from movement import Movement
#create a movement class and select a backgroun subtractor
mov=Movement()
backsub=mov.background_subtractor(algo="MOG2", varThreshold=10)
#use the background subtractor to calculate movement (foreground)
mov.calculate(Video=myvid, method="background", function=backsub, inplace=True)
```
The `method` parameter is for determining whether to use background subtraction or optical flow (see below). If
if `inplace` is `True` then the calculated masks will be written to `myvid.masks` attribute. If is possible to 
set `inplace` to `False`, then a list of ndarrays will be returned. This is useful if you want to try several 
different methods or parameters without re-generating the frames. 

### Optical flow

In addition to background subtraction two different methods of dense optical flow methods are also implemented. Their
usage is quite similar to background subtraction. 

```python
mov=Movement()
dense_flow=mov.dense_flow(algo="farnebeck", **kwargs) #optional key word arguments see below for defaults. 
mov.calculate(Video=myvid, method="optical", function=dense_flow, get="magnitude", inplace=True)
``` 

There is an additional get parameter that is only used in optical flow. The options are `magnitude`, `angle` and `both`
if both is selected a stacked ndarray is returned, where the first z stack (`[:,:,0]`) is magnitude and 
the second (`[:,:,1]`) is the angle of the movement in degrees. The implemented methods and their default values are:

### farneback

For computing a dense optical flow using the Gunnar Farneback's algorithm.

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

## Object

Object detection is for calculating different attributes of the objects in the video. Currently only one object
per frame is supported as there is no tracking of object through different frames. The properties of these objects
are calculated by using watershed segmentation. In order for segmentation to work each frame must be separated into
foreground and background using a threshold. These methods are implemented within the object class. 

```python
from object import Watershed
seg=Watershed()
#calculate appropriate thresholds for each frame
seg.threshold(Video=myvid, method="otsu", cores=1, inplace=True, **kwargs) 
seg.segmentation(myvid, inplace=True, cores=1, **kwargs)
seg.properties(myvid, cores=1, **kwargs)
```

Similar to other methods above if `inplace` is `True` the threshold values will be in `myvid.threshold` and 
segmentation masks will be under `myvid.masks`. Since segmentation is a computationally intensive process you 
can specify how many parallel processes you want to use with the `cores` argument. 

After segmentation calculation you can measure different attributes of the detected object(s). All these parameters
and their default values are described below. 

### Thresholding methods

#### isodata

Calculate threshold based on ISODATA method, also known as Ridler-Calvard method or inter-means. The lowest value that satisfies the equality 

```threshold=(image[image <=threshold]).mean()+image[image > threshold].mean())/2```

Separating the image into 2 groups of pixels where the intensity is midway between these groups. 

+ nbins: 256, number of bins 256 is the reccomended value of 8 bit images. 

#### li

Compute Li's iterative Minimum Cross Entropthy method

+ tolerance: None, finish computation when the change in threshold in an iteration is less than this value, the default is 1/2 smallest difference between intesity values. 

#### otsu

Return a threshold value based on Otsu's method. 

+ nbins: 256, number of bins this is the reccomended value for 8 bit images

#### multi_otsu

generate classes-1 threshold values to divide the image using otsu's method. This is useful if you have 
very bright spots and you wan to take not the nth class but the n-1th class as your high points. 

+ classes: 3, integer
+ nbins: 256, number of bins this is the reccomended value for 8 bit images

#### yen

Return threshold value based on Yen’s method.

+ nbins: 256, number of bins this is the reccomended value for 8 bit images


### Segmentation parameters

Compact watershed algorithm as implemented in [scikit-image](scikit-image.org/) is being used in this class. The parameters are:

+ markers: the output of threshold method in the object class, you are already passing this so do not use it in `**kwargs`
+ connectivity: None, ndarray whose dimensions are the same as the image and non-zero elements indicate neighbors for connection
+ offset: None, array_like-offset of the connectivity
+ mask: None, array_like same shape as image 
+ compactness: 0, float-larger values result in more regularly shaped basins
+ watershed_line: False, whether to draw the watershed lines as a single pixel wide line. Turning this on might negatively effect labelling downstream

### Calculated properties

By default all of these measures are calculated. You can pick and choose and can pass these as a list of strings
using the `properties` keyword argument. 

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

# Analysis

You can also use this package to perform the above analysis in an automated manner. You would need to specify algorrithms
and their parameters (if you wish, see above for defaults). The only limitation is using the analysis.py script  
currently you cannot use background subtraction and optical flow class getters and setters. 

## Running

There is an `analysis.py` script that takes a `yaml` file with different parameters and runs the above analysis per 
video file specified. The specified outputs (an excel file with results, an optional mp4 and an optional hdf5 file) are then
moved to an output directory along with the `yaml` file used for reproducibility. Here are the command line options, you can also view these using

python analysis.py --help

-f or --filename : file path for file mode usage  
-d or --directory : directory for directory mode usage  
-t or --use_object_tracking : use object tracking (this is still under development) uses feature matching using the ORB algorithm and mask warping to match framex to framex-1  
-y or --config_yaml : path for the config file for function parameters. The default values are provided in config.yaml (see below)  
-c or --cores : # of sub processes to spawn for determining masks and object tracking.  
-o or --output : the name of the output folder  
-e or --extension : the file extension for the video, this uses ffmpeg in the background so anything supported by ffmpeg is also supported. default: avi  

below is an example of an object detection analysis `config.yaml` file. 
```yaml
video:
  invert: false
  denoise:
    disk: 2
  adjust:
    method: gamma
    method_params:
      gain: 1 
  normalize:
    reference_frame: 0

# analysis parameters
method: object_detection
threshold:
  algorihtm: otsu
  algorithm_params: 
    nbins: 255
segmentation_params: 
  compactness: 2

cores: 1 

calculate: 
  properties: 
    - area
    - bbox_area
    - convex_area
    - eccentricity
  cache: true
  fill_holes: false
  get_largest: true

output:
  video:
      periodicity: 10 # use every nth frame
      FPS: 10 #frames per second
      size:
        width: 6 #inches
        height: 3
  raw:
```

This file specifies a lot of parameters. If one wanted to use the default parameters the `config.yaml` can be
condensed to:

```yaml
method: object_detection
threshold:
    name: otsu
output:
    video:
    raw:
```

And a minimal example for background subtraction would look like:

```yaml
method: movement_detection
type: background_subtraction
algorithm:
  name: MOG2
```

And for optical flow:

```yaml
method: movement_detection
type: optical_flow
algorithm:
  name: farnebeck
  return: magnitude
```

Finally below is a list of all possible options and mandatory ones that can be passed to `config.yaml`

### For Video processing

```yaml
video:
  invert: #default false
  denoise:
    disk: 
  adjust:
    method: #mandatory if adjust is used
    method_params: 
      # a collection of key value pairs go here
  normalize:
    reference_frame: #default is 0
```

### For movement detection

```yaml
method: movement_detection #mandatory
type: # either background_subtraction or optical_flow mandatory if method is movement detection
algorithm: #mandatory
    name: #mandatory see above
    algo_params:
      #parameters go here see above for method specific parameters
    return: #mandatory if optical flow is used
```

### For object detection

```yaml
method: object_detection #mandatory
threshold:
  algorihtm: #mandatory
  algorithm_params: 
    # add method specific parameters here
segmentation_params: 
  # add watershed specific parameters here
cores: #this is used for both segmentation and feature calculation default 1
calculate:
  properties: # see readme for a complete list
    # this is a yaml list not key value
  cache: # whether to cache values true is faster but uses more memory
  fill_holes: # if there are holes in the object (dark or bright spots) default false
  get_largest: #get the largest object in the frame default false
  min_size: #ignored if get largest is true default 20000 pixels 
```

### For optional outputs

```yaml
output:
  video:
      periodicity: # use every nth frame default 30
      FPS: #frames per second default 10
      size:
        width:  #inches default 6
        height: # default 3
  raw: # the presence of this key indicates whether to return the hdf5 file. 
```

# Future directions

I think the threshold calculations should also be added to the hdf5 file. Additionally multi object support would
come in handy. Those methods will be implemented in the future. If you have any questions or bug reports please 
create an issue and I will respond as fast as I can. 




