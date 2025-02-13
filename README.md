# SSQN - SARS-CoV-2 sewage Quality control and Normalization 
SSQN - (**S**ARS-CoV-2 **S**ewage **Q**uality control and **N**ormalization) is a tool for quality control and normalization of SARS-CoV-2 biomarkers obtained from sewage water.

## Installation from Github
SSQN is completely written in Python 3. We recommend using python 3.8.

To install SSQN using pip
```
pip install git+https://github.com/agblum/ssqn.git
```

## Environment Setup for SSQN

### 1. Install Conda (Recommended)
 Conda is a powerful package and environment manager for Python. If you don’t have it installed, you can download it from [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/).

### 2. Install Git
Git is required to clone this repository and manage updates. You can download it from [git-scm.com](https://git-scm.com/).

### 3. Create and Activate a Conda Environment
Run the following commands to create and activate a Conda environment:

```sh
conda create -n ssqn python==3.10
conda activate ssqn
```

### 4. Install the `SSQN` Package
Once your environment is active, install the `SSQN` package directly from GitHub:

```sh
pip install git+https://github.com/agblum/ssqn.git
```
## Usage 

```sh
ssqn.py --help
```

## Example

You will need an excel file containing your wastewater-based epidemiology (WBE) data.
Then use:

```
ssqn.py -i [YOUR_WBE_DATA.xlsx] -o [OUTPUT_FOLDER] --rerun_all
```
- --rerun_all [Optional]: Forces the script to reprocess all data, even if it was processed before.

## Citation 
SSQN can be used and adapted for non-commercial or commercial usage following the CC-BY license. Credit should be given to the authors by including the following citation


> From wastewater to GIS-based reporting: the ANNA-WES data model for reliable biomarker tracking in wastewater and environmental surveillance. Kau & Uchaikina et al., 2025



## Flowchart

![Flow_chart_SSQN.tif](data/img/Flow_chart_SSQN.png)
