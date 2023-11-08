# -*- coding: utf-8 -*-
"""Brain-to-Speech Synthesis Project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/14uLWD8cXQA0f5vrEuCG9xXwBtU-0DcFT

# Milestone 1: Data acquisition, Data preparation

# 1. Data Source, Installation and Data Integration

The data that will be used in the development of this project is the [Dataset of Speech Production in intracranial Electroencephalography](https://www.nature.com/articles/s41597-022-01542-9), this dataset can be downloaded from [here](https://osf.io/nrgx6/download) and then was uploaded to google drive.

The dataset is based on 10 participants reading out individual words while being measured his intracranial EEG from a total of 1103 electrodes. It has a high temporal resolution and coverage of a large variety of cortical and sub-cortical brain regions, can help in understanding the speech production process better.
"""

# Install every library that we will need for the development of the project

!pip install numpy scipy scikit-learn pandas pynwb nilearn nibabel RutishauserLabtoNWB pytorch-lightning --quiet

import numpy as np
import scipy
import sklearn
import pandas as pd
import pynwb
import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib
from nilearn import plotting
import RutishauserLabtoNWB as RLab

import pytorch_lightning as pl

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import random_split, DataLoader

from torchmetrics import Accuracy

from torchvision import transforms

# Give permission to acces Google Drive cause there is where the Zip File is
from google.colab import drive
drive.mount('/content/drive')

!ls "/content/drive/My Drive/"

# Let's unzip the file
!unzip -o  "/content/drive/My Drive/SingleWordProductionDutch-iBIDS.zip"

# Let's check if the file is already unziped
!ls

# Let's lists the files and directories in the current directory
!ls "SingleWordProductionDutch-iBIDS"

"""## 1.2  We Clone the repository with the Scripts, so we can work with the intracranial EEG data"""

!git clone https://github.com/neuralinterfacinglab/SingleWordProductionDutch.git

"""# 2. Data Exploration and Visualization

Our dataset has a structure that follows the BIDS (Brain Imaging Data Structure) format, which is a standard in organizing neuroimaging and neurophysiology data.

So we'll approach the data in the next way:
1. Metadata Exploration
2. Individual Participant Data
3. Derivatives Data

## 2.1. Metadata Exploration
The root folder contains:
- metadata of the participants (participants.tsv)
- subject specific data folders (i.e., sub-01)
- derivatives folder

### 2.1.1 README
"""

# Read the README in case some important information is needed for the dataset evaluation

with open("SingleWordProductionDutch-iBIDS/README", "r") as file:
    readme_contents = file.read()

print(readme_contents)

"""### 2.1.2 Dataset Description"""

# Read the dataset description as an informative
import json
with open("SingleWordProductionDutch-iBIDS/dataset_description.json", "r") as file:
    dataset_description = json.load(file)

# Display the contents of the JSON file
dataset_description

"""### 2.1.3 Participants"""

# Read for general demographic information of participants
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

# Read and display participants.tsv
participants_tsv = pd.read_csv("SingleWordProductionDutch-iBIDS/participants.tsv", sep='\t')
participants_tsv

# Read to understand the metadata of "participants.tsv"

# Open and read participants.json
with open("SingleWordProductionDutch-iBIDS/participants.json", "r") as file:
    participants_json = json.load(file)

participants_json

# Create a dataframe of the dictionary for better understanding

# Convert nested dictionary to a list of dictionaries for creating a DataFrame
participants_json_list = []
for key, value in participants_json.items():
    row = {'key': key}
    row.update(value)
    participants_json_list.append(row)

# Convert to DataFrame
df = pd.DataFrame(participants_json_list)
df

"""### 2.1.4 Derivatives"""

!ls "SingleWordProductionDutch-iBIDS/derivatives"

"""## 2.2 Individual Participant Data
The subject specific folders contain .tsv files with information about:
- the implanted electrode coordinates (_electrodes.tsv)
- recording montage (_channels.tsv)
- event markers (_events.tsv)
- The _ieeg.nwb file contains three raw data streams as timeseries (iEEG, Audio and Stimulus), which are located in the acquisition container.
- Descriptions of recording aspects and of specific .tsv columns are provided in correspondingly named .json files (i.e., participants.json).

We will choose one participant for the development of the project, and with his data we will realize the training, validation and testing for the set of a single speaker.

The election of the individual participant will be random, so the selected participant is **sub-01**

### 2.2.1 The implanted electrode coordinates
"""

# 1. Load the electrodes.tsv for sub-01
electrodes_tsv_path = "/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_space-ACPC_electrodes.tsv"
electrodes_data = pd.read_csv(electrodes_tsv_path, sep='\t')
display(electrodes_data)

def value_plot(df, columns, figscale=1):
    for col in columns:
        df[col].plot(kind='line', title='Values of electrodes in sub-01',figsize=(5*figscale, 2.5*figscale), label=col)

    plt.gca().spines[['top', 'right']].set_visible(False)
    plt.legend(loc='best')

electrodes_chart = value_plot(electrodes_data, ['x', 'y', 'z'])
display (electrodes_chart)

def histogram(df, columns, num_bins=20, figscale=1):
    for col in columns:
        df[col].plot(kind='hist', bins=num_bins, title="Distribution of electrodes in sub-01",figsize=(5*figscale, 2.5*figscale), alpha=0.5, label=col)

    plt.gca().spines[['top', 'right']].set_visible(False)
    plt.legend(loc='best')

electrodes_distributionchart = histogram(electrodes_data, ['x', 'y', 'z'])
display(electrodes_distributionchart)

"""### 2.2.2 Recording montage"""

# 2. Load the channels.tsv for sub-01
channels_tsv_path = "/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_channels.tsv"
channels_data = pd.read_csv(channels_tsv_path, sep='\t')
display(channels_data)

"""### 2.2.3 Event markers"""

# 3. Load the events.tsv for sub-01
events_tsv_path = "/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_events.tsv"
events_data = pd.read_csv(events_tsv_path, sep='\t')
display(events_data)

"""### 2.2.4 The _ieeg.nwb file (iEEG, Audio and Stimulus)"""

# 4. Load the .nwb file
# We use NWBHDF5IO to read the data stored in NWB files, accessing and analyzinge the neurophysiological data inside
from pynwb import NWBHDF5IO

ieeg_nwb_path = "/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_ieeg.nwb"
with NWBHDF5IO(ieeg_nwb_path, 'r') as io:
  nwbfile = io.read()

  # List the names of all data interfaces in the file
  print(nwbfile.acquisition)

  # Extract data for each interface
  audio_data_sample = nwbfile.acquisition['Audio'].data[:15]
  stimulus_data_sample = nwbfile.acquisition['Stimulus'].data[:15]
  ieeg_data_sample = nwbfile.acquisition['iEEG'].data[:15]

  print("Audio data:", audio_data_sample)
  print()
  print("Stimulus data:", stimulus_data_sample)
  print()
  print("iEEG data (first 5 channels):", ieeg_data_sample[:, :5])

import h5py #HDF5 is designed to store and organize large amounts of numerical data

with h5py.File(ieeg_nwb_path, 'r') as nwbfile:

# Print the root-level keys in the HDF5 file
  print(list(nwbfile.keys()))

"""### 2.2.5 Descriptions of recording aspects and of specific .tsv columns"""

# 5. Load the first JSON file

import json
path_to_json = "/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_space-ACPC_coordsystem.json"
with open(path_to_json, 'r') as json_file:
    data_description = json.load(json_file)

print(json.dumps(data_description, indent = 2))

# 5. Load the second JSON file

path_to_json2= '/content/SingleWordProductionDutch-iBIDS/sub-01/ieeg/sub-01_task-wordProduction_ieeg.json'

with open(path_to_json2, 'r') as json_file:
    data = json.load(json_file)

print(json.dumps(data, indent=4))

"""## 2.3 Derivatives Data
The derivatives folder contains:
- the pial surface cortical meshes of the right (_rh_pial.mat) and left (_lh_pial.mat) hemisphere
- the brain anatomy (_brain.mgz)
- the Destrieux atlas (_aparc.a2009s + aseg.mgz)
- a white matter atlas (_wmparc.mgz) per subject, derived from the Freesurfer pipeline.
"""

!ls SingleWordProductionDutch-iBIDS/derivatives

"""### 2.3.1 Pial Surface Data"""

# Explore Pial Surface Data
import scipy.io

rh_pial_path = "/content/SingleWordProductionDutch-iBIDS/derivatives/sub-01/sub-01_rh_pial.mat"
lh_pial_path = "/content/SingleWordProductionDutch-iBIDS/derivatives/sub-01/sub-01_lh_pial.mat"

rh_pial = scipy.io.loadmat(rh_pial_path)
lh_pial = scipy.io.loadmat(lh_pial_path)

# Let's inspect the keys and structure of the loaded data
print(rh_pial.keys())
print(lh_pial.keys())

"""### 2.3.2 Brain Anatomy"""

# Explore Brain Anatomy

brain_data_path = "/content/SingleWordProductionDutch-iBIDS/derivatives/sub-01/sub-01_brain.mgz"
brain_data = nib.load(brain_data_path)

# Display the shape of the data
print("Data shape:", brain_data.shape)

# Display header information
print(brain_data.header)

# Get the actual data as a numpy array (if needed)
brain_numpy_data = brain_data.get_fdata()

# Extract a 2D slice
axial_slice = brain_numpy_data[:, :, brain_numpy_data.shape[2] // 2]

plt.imshow(axial_slice.T, cmap="Blues", origin="lower")
plt.title("Axial Lower Slice")
plt.show()

# Extract a 2D slice
axial_slice = brain_numpy_data[:, :, brain_numpy_data.shape[2] // 2]

plt.imshow(axial_slice.T, cmap="gray", origin="upper")
plt.title("Axial Upper Slice")
plt.show()

"""### 2.3.3 The Destrieux atlas"""

destrieux_atlas_path = "/content/SingleWordProductionDutch-iBIDS/derivatives/sub-01/sub-01_aparc.a2009s+aseg.mgz"
destrieux_atlas_data = nib.load(destrieux_atlas_path)

# Get the data array from the atlas
atlas_array = destrieux_atlas_data.get_fdata()

# Print the shape of the data to understand its dimensions
print(atlas_array.shape)

# Print header information to understand metadata
print(destrieux_atlas_data.header)

# Convert the data to a 3D numpy array
atlas_img = np.asarray(atlas_array, dtype=np.int32)

# Display the atlas using nilearn's plotting function
plotting.plot_roi(destrieux_atlas_data, draw_cross=False, title="Destrieux Atlas")
plotting.show()

"""### 2.3.4  A white matter atlas"""

import nibabel as nib

wm_atlas_path = "/content/SingleWordProductionDutch-iBIDS/derivatives/sub-01/sub-01_wmparc.mgz"
wm_atlas_data = nib.load(wm_atlas_path)

# Extract data array from the atlas
wm_array = wm_atlas_data.get_fdata()

# Print the shape of the data
print(wm_array.shape)

# Print header information for metadata understanding
print(wm_atlas_data.header)

import numpy as np
from nilearn import plotting

# Convert the data to a 3D numpy array
wm_img = np.asarray(wm_array, dtype=np.int32)

# Display the atlas using nilearn's plotting function
plotting.plot_roi(wm_atlas_data, draw_cross=False, title="White Matter Atlas")
plotting.show()

"""# 3. Preparing data for training
- As we mention before, we filter the data so we are only using a single speaker sub-01.

Given the content of the NWBFile, there are three types of data under de acquisition field:
- Audio <class 'pynwb.base.TimeSeries'>
- Stimulus <class 'pynwb.base.TimeSeries'>
- iEEG <class 'pynwb.base.TimeSeries'>

iEEG stands for intracranial electroencephalography. It is a type of electroencephalography (EEG) where electrodes are placed directly on the exposed surface of the brain to record electrical activity. This is in contrast to traditional EEG where electrodes are placed on the scalp.

iEEG data is particularly valuable. Speech production involves multiple regions of the brain, including the motor cortex, Broca's area, and others. The high spatial resolution of iEEG allows for the nuanced study of how these regions interact during the task. This makes it an essential dataset for understanding brain mechanisms involved in speech, which can be of significance in our project.

# 3.1 Preparing audio
"""

audio_data_np = np.array(audio_data_sample)
max_amplitude = np.max(np.abs(audio_data_np))
audio_data_normalized = audio_data_np / max_amplitude
audio_tensor = torch.tensor(audio_data_normalized, dtype=torch.float32)
batch_size = 1  # We might adjust the batch size
audio_tensor = audio_tensor.view(batch_size, -1)
audio_array = audio_tensor.squeeze().numpy()  # Squeeze removes dimensions of size 1 (in case batch_size is 1)
# Plot the audio waveform
plt.figure(figsize=(12, 4))
plt.plot(audio_array)
plt.xlabel('Sample')
plt.ylabel('Amplitude')
plt.title('Audio Waveform')
plt.show()

"""# 3.2 Preparing iEEG"""

ieeg_data_np = np.array(ieeg_data_sample)
max_amplitude_ieeg = np.max(np.abs(ieeg_data_np))
ieeg_data_normalized = ieeg_data_np / max_amplitude_ieeg
ieeg_tensor = torch.tensor(ieeg_data_normalized, dtype=torch.float32)
# Visualize iEEG data
plt.figure(figsize=(8, 6))
plt.imshow(ieeg_tensor.T, aspect='auto', cmap='viridis', origin='lower')
plt.xlabel('Time Step')
plt.ylabel('Channel')
plt.title('iEEG Data Visualization')
plt.colorbar(label='Amplitude')
plt.show()