# Image2Structure - Latex

## Dataset description
We introduce Image2Structure, a dataset to evaluate the capabilities of multimodel models to learn the structure of a document. This subdataset focuses on Latex code. The model is given an image of the expected output with the prompt:
```Prease provide the LaTex code used to generate this image. Only generate the code relevant to what you see. Your code will be surrounded by all the imports necessary as well as the begin and end document delimiters.```
An additional message is added if assets are available:
```
The following assets can be used:
 - assets/cs/1_log.png
 - ...
 ```
 The assets are provided under the assets folder for each subject. The subjects were collected on ArXiv and are: eess, cs, stat, math, physics, econ, q-bio, q-fin.
 
 The dataset is divided in 5 categories:
* equations
* figures
* tables
* algorithms
* code