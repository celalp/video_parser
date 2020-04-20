# Object Detection Branch

This branch is for detecting individual objects in each frame and calculating different attributes. Because of this it is signficantly slower than movement detection. To overcome this limitaiton for mask generation and attribute calculation you can speficify the number of cores to use. 

# Running

Object detection is done through multi-otsu segmentation followed by watershed algorithm. If you need other methods implemented please create an issue with your specific use case and what algorithms you need. 

Video I/O is handled through [opencv](https://opencv.org/) but most other image manipulation and object detection is done through [scikit-image](https://scikit-image.org/). 

Here are the command line options, you can also view these using 

```bash
python analysis.py --help
```

`-f` or `--filename` : file path for file mode usage  
`-d` or `--directory` : directory for directory mode usage  
`-t` or `--use_object_tracking` : use object tracking (this is still under development) uses feature matching using the ORB algorithm and mask warping to match frame<sub>x</sub> to frame<sub>x-1</sub>  
`-y` or `--config_yaml` : path for the config file for function parameters. The default values are provided in `config.yaml`
(see below)  
`-c` or `--cores` : # of sub processes to spawn for determining masks and object tracking.  
`-o` or `--output` : the name of the output folder  
`-e` or `--extension` : the file extension for the video, this uses ffmpeg in the background so anything supported by ffmpeg is also supported. default: `avi`

## parameters

Here are the default parameters in the `config.yaml` file with description below. 

```yaml
frames:
  return_denoized: true # use gaussian kernel denoising 
  disk_size: 2 # disk size for denoising
  invert: false # invert the values
masks:
  levels: 3 #if there are overexposed regions in the images use 4
tracking:
  min_value: 10 # min number of interesting points to use
  normalize: true # normalize the histogram of frame x using frame x-1
  reference_frame: 0 # subtract the value of this from every other frame
calculate:
  remove_background: true # only use masked area
  fill_holes: false # fill holes in the objects
  min_size: 20000 # minimum object size so we can ignore small debris
  attributes:
    - area #mask area
    - bbox_area # area of the bounding box
    - convex_area # area of the convex hull
    - eccentricity # how eliptical is the mask
    - extent # area of bounding box/area of mask
    - local_centroid # centre of mass of the mask
    - major_axis_length # of the bounding ellipse
    - minor_axis_length # of the bounding ellipse
    - perimeter # of the mask
    - solidity # how rectangular is the mask
    - weighted_local_centroid # centre of mass of the mask weighed by pixel intensity 
  cache: true # faster but uses more memory
write_video:
  write: true
  what:
    - overlay
    - mask
    - frame #using pseudo color
  periodicity: 10 # use every nth frame 
  FPS: 10 #frames per second
  size:
    width: 3 #inches
    height: 3
``` 

So a standard run will look like this for single file mode. 

```bash
python analysis.py -f myvideo.avi -y config.yaml -o myoutput -c 5 
```

This will generate myoutput.xlsx with a single sheet named myvideo. 

If using the directory mode:

```bash
python analysis.py -d myfiles -y config.yaml -o myoutput -c 5
```

This will generate a folder called myoutput. Inside this folder there will be another folder per video. Within these 
folder there will be multiple files. These are:

1. results.xlsx: An excel file with 2 sheets, the first one is called "raw" has the calculted values. The other one is 
called "reference_removed" and has the value of the reference frame removed from each of rows. The columns depends on 
what has been specified in the `config.yaml` file (see above). In addition to those columns there will be an intensities 
column that is the sum of all pixels in the mask and label column which can be ignored for now. That column will be used 
for multi object tracking in the future.

2. An mp4 video for each feature specified. 

3. the config.yaml file for the run for record keeping. 

You can use the values in the excel file to visualize using your favourite graphing tools. 

Please let me know if you have any questions or issues. 

