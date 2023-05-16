# -*- coding: utf-8 -*-
"""
Example of remote control of DataLab current session,
from a Python script running outside DataLab (e.g. in Spyder)

Created on Fri May 12 12:28:56 2023

@author: p.raybaut
"""

# %% Importing necessary modules

# NumPy for numerical array computations:
import numpy as np

# DataLab remote control client:
from cdl.remotecontrol import RemoteClient

# %% Connecting to DataLab current session

datalab = RemoteClient()
datalab.connect()

# %% Executing commands in DataLab (...)

z = np.random.rand(20, 20)
datalab.add_image("toto", z)

# %% Executing commands in DataLab (...)

x = np.array([1.0, 2.0, 3.0])
y = np.array([4.0, 5.0, -1.0])
datalab.add_signal("toto", x, y)

# %% Executing commands in DataLab (...)

datalab.compute_derivative()

# %% Executing commands in DataLab (...)

datalab.switch_to_panel("image")

# %% Executing commands in DataLab (...)

datalab.compute_fft()