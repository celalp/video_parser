# Parse gut slice videos

This is the mini python package I used to analyse the initial batch of gut slice videos. The whole thing consists of 3 
python files. `parse_video.py` and `utils.py` are the workhorse files and `analysis.py` is the executable script.

# Installation

This package was written in python 3.7 so that needs to be installed. See [python documentation](https://www.python.org/) 
for OS specific installation instructions. 

## Dependencies

This package has several dependencies, they are in the `requriements.txt` package. After python installation those can be 
installed using `pip`. If `pip` is not installed in your system you can use [these instructions](https://pip.pypa.io/en/stable/installing/) 
to install `pip` and run the command: 

```bash
pip install -r requriements.txt
```

Keep in mind that if you have multiple versions of python installed (python2 vs 3 or python 3.5 vs 3.6) you might want to 
follow [different instructions](https://stackoverflow.com/questions/2812520/dealing-with-multiple-python-versions-and-pip).

# Running

There are 2 mutually exclusive analysis modes. Directory and file. Directory mode takes a directory path and iterates over
all the files in that specific location that end with .avi. File mode takes a single file. 

Here are the command line options, you can also view these using 

```bash
python analysis.py --help
```


`-f` or `--filename` : file path for file mode usage  
`-d` or `--directory` : directory for directory mode usage  
`-t` or `--use_object_tracking` : use object tracking (this is still under development) but uses feature matching using the ORB algorithm  
and mask warping to match frame_x to frame_{x-1} 
`-y` or `--config_yaml` : path for the config file for function parameters. The default values are provided in `config.yaml`
(see below)  
`-c` or `--cores` : # of sub processes to spawn for determining masks and object tracking.  
`-o` or `--output` : the name of the output file desired will be written in the current directory and 
xlsx will be added to the file name.  

## parameters

Here are the default parameters in the `config.yaml` file with description below. 

```yaml
frames:
  return_denoized: true # use gaussian kernel denoising 
  disk_size: 2 # the radius for above
  invert: false # invert values after converting the color frames to grayscale
masks:
  quantile: 0.15 # lower threshold for watershed algorithm. 
tracking:
  min_value: 10 # min number of features to detect
  normalize: true # normalize frame x histogram using frame x-s
  reference_frame: 0 # use this frames mask and the starting point
calculate:
  remove_background: true # only use the detected object (the mask area)
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

This will generate myoutput.xlsx with a sheet in the excel file for every file in the directory that ends with `.avi`.

Each sheet will have 4 columns, 

**intensity**: total pixel intensity for each frame (w/ or w/o background removal depending on settings)  
**mask**: total mask area  
**intensity_noref**: total pixel intensity for each frame minus the total intensity of the reference frame  
**mask_noref**: total mask area minus the mask area of the reference frame  


You can then use these values to visualize using your favourite graphing tools. 


Please let me know if you have questions or issues. 

Alper Celik
