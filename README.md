# Movement Detection Branch

This branch is for detecting movement from one frame to the next. It is considerably faster than the object detection branch because we do not concern ourselves with what is moving. 

# Installation

Please see the master branch readme for instructions.

# Running

Two main forms of analysis are implemented in this branch. One is movement detection by background subtraction and the other is through optical flow. Each forms also have different algorithms that are available for analysis. These algorithms are directly from [opencv](https://opencv.org/). I did not use cuda enabled algorithms for compatibility purposes. If you need these algorithms implemented please create an issue with a description of your use case and hardware. 

To see available options you can type:

```bash
python analysis.py --help
```
The run time flags are below:

`-f` or `--filename` : file path for file mode usage  
`-d` or `--directory` : directory for directory mode usage  
`-y` or `--config_yaml` : path for the config file for function parameters. The default values are provided in `config.yaml`
(see below)  
`-o` or `--output` : the name of the output folder  
`-e` or `--extension` : the file extension for the video, this uses ffmpeg in the background so anything supported by ffmpeg is also supported. default: `avi`

## parameters

Here are the default parameters in the `config.yaml` file with description below. 

```yaml
method: backgroud_remove #the other option is optical_flow
algorithm: MOG2 # see below
method_parameters:
   detectShadows: false
   history: 10
apply_parameters:
   learningRate: 0.5
invert_frame: false
invert_mask: false
video:
   write: true
   size: #inches
      width: 3
      height: 3
   FPS: 10
   periodicity: 10
``` 

Currently quite a few background subtraction methods are implemented. If no options are specified under `method_parmeters` default values are used. These are usually good starting points but you might want to tweak the configuration depending on your needs. 

Available background subtraction methods are:

+ MOG2
+ MOG
+ KNN
+ GSOC
+ LSBP
+ GMG
+ CNT

Please see opencv documentation about available parameters and default values. 

Available optical flow methods are:

+ Dense optical flow using Farnabeck
+ Sparse optical flow with Lucas-Kanade method with pyramids. It also uses ShiTomasi corner detection for feature idenfitication.

```yaml
#TODO
```

So a standard run will look like this for single file mode. 

```bash
python analysis.py -f myvideo.avi -y config.yaml -o myoutput
```

This will generate myoutput.xlsx with a single sheet named myvideo. 

If using the directory mode:

```bash
python analysis.py -d myfiles -y config.yaml -o myoutput
```

This will generate a folder called myoutput. Inside this folder there will be another folder per video. Within these 
folder there will be multiple files. These are:

1. results.xlsx: An excel file with a single sheet. 
  + if background subtraction is used this contains the #frame number and the number of pixels that are detected to be "foreground"
  + if optical flow is used #TODO

2. An mp4 video for each feature specified. 

3. config.yaml file for the run for record keeping. 

You can use the values in the excel file to visualize using your favourite graphing tools. 

Please let me know if you have any questions or issues. 

