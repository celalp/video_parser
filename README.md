# Parse gut slice videos

This is the mini python package I used to analyse the initial batch of gut slice videos. There are 2 branches for different
kinds of analysis. Object detection is for detecting single object in the video and tracking different attibutes throughout. 
Movement detection does not concern itself with objects and only keeps track of how much movment there is. 

This package was written in python 3.7 so that needs to be installed. See python documentation for OS specific installation 
instructions.
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

# Analysis

For different analysis modes one needs to switch between different branches. Please see readme files in those branches 
for analysis type specific instructions. To switch between different analysis modes you can use `git checkout` command
as shown below: 

For object detection use:

```bash
git checkout object_detection
``` 

and follow the instruction on the readme there. 

Similarly, for movement detection use:

```bash
git checkout movement_detection
``` 

# Running

There are 2 mutually exclusive run modes. Directory and file. Directory mode takes a directory path and iterates over
all the files in that specific location that end with specified format (default .avi). File mode takes a single file. 

You can see analysis type command option using

```bash
python analysis.py --help
```
The analysis generates a folder specified in with the `-o` flag. This folder contains an excel file that has the resutls (depending on the analysis more speficfied) an mp4 file for visual expection of the analysis and the config.yaml file used for reproducibility. 

See the other branches for detailed explanantion of the analyses conducted. 

