"""
Author: Thais Silva Abelha
Email: thais.silva.abelha@gmail.com

This work was done during a undergraduated research "Comparing different methods of position
reconstruction considering 1D readout of GEM detectors"
"""

import numpy as np
import math
import pandas as pd
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

from constants import (
    STRIP_WIDTH,
    PITCH,
    FIRST_STRIP_POSITION,
    LAST_STRIP_POSITION,
    FIRST_CLOUD_POSITION,
    LAST_CLOUD_POSITION,
    SEED,
    THRESHOLD,
    STD_DEVIATION_OF_THE_NOISE,
    NUMBER_OF_ELECTRON_CLOUDS,
)


from DataHandler.create_dataframe_discrete_electron_cloud import create_a_dataframe

from plots_discrete_electron_cloud.plot_normal import plot_normal
from plots_discrete_electron_cloud.plot_cluster import plot_cluster
from plots_discrete_electron_cloud.plot_errors import plot_errors
from plots_discrete_electron_cloud.plot_hist2d import plot_hist2d


#%%
def x_projection(df):
    xprojection = df.groupby("x")["E"].sum().reset_index()
    Bin = xprojection.iat[1, 0] - xprojection.iat[0, 0]
    xprojection["E"] = xprojection["E"] / (xprojection["E"] * Bin).sum()
    return xprojection["x"], xprojection["E"]


def interpolation(x_coordinate, charge_density):
    f = interp1d(x_coordinate, charge_density, kind="cubic")
    n = 50
    x = np.linspace(
        x_coordinate[0],
        x_coordinate[len(x_coordinate) - 1],
        num=n * len(x_coordinate),
        endpoint=True,
    )
    E = f(x)
    return x, E


def Func_Normal(x, x0, sigma):
    return (1 / (sigma * np.sqrt(2 * math.pi))) * np.exp(
        -((x - x0) ** 2) / (2.0 * sigma**2)
    )


strip_centers = np.arange(FIRST_STRIP_POSITION, LAST_STRIP_POSITION, PITCH)
electron_cloud_centers = np.arange(
    FIRST_CLOUD_POSITION, LAST_CLOUD_POSITION, PITCH / 10
)


#%%############################################################################
# Reading file with the electron cloud data which is a Garfiled++ output
###############################################################################
file = "data/evt1.txt"
electron_cloud_df = pd.read_csv(file, sep="\s+", header=None)
electron_cloud_df.rename({0: "x", 1: "y", 2: "E"}, axis=1, inplace=True)
electron_cloud_df[["x", "y"]] = electron_cloud_df[["x", "y"]] / 1000


#%%############################################################################
# Input data: Electron Cloud -> Electron cloud projection in x direction
# -> Interpolation of the data
###############################################################################
x_coordinate, charge_fraction = x_projection(electron_cloud_df)
x_coordinate_interpolate, charge_fraction_interpolate = interpolation(
    x_coordinate, charge_fraction
)

"""Since we are going to fit a gaussian function, we can try those expressions for getting an approximation
for the mean and sigma values of the fit"""

mean = sum(x_coordinate * charge_fraction) / sum(charge_fraction)
sigma = np.sqrt(
    sum(charge_fraction * (x_coordinate - mean) ** 2) / sum(charge_fraction)
)
popt, pcov = curve_fit(Func_Normal, x_coordinate, charge_fraction, p0=[mean, sigma])

###############################################################################
# we fit on the electron cloud generated by Garfield++ software, just too see how gaussian it is
# And the s value is the standard deviation of the gaussian function
# We modeled noise which comes from the eletronics as a gaussian distribution
# and its standard deviation is represented by STD_DEVIATION_OF_THE_NOISE
##############################################################################
STD_DEVIATION_OF_ELECTRON_CLOUD_FIT = popt[1]  # popt[1] is the fit result for sigma
###############################################################################
# Plotting the original 2D data and its projection in x direction
###############################################################################
plot_hist2d(
    electron_cloud_df["x"],
    electron_cloud_df["y"],
    electron_cloud_df["E"],
    len(x_coordinate),
)
plot_normal(x_coordinate, charge_fraction, strip_centers, popt, pcov)

#%%############################################################################
# Calculating the Collected Charge considering the noise, using Monte Carlo's method
# A clustarization algorithm, made especially for this problem, separetes the electron cloud signal from the noise
# and the Errors of Position Reconstruction are calculetade for 1000 events
###############################################################################
df = create_a_dataframe(
    STRIP_WIDTH,
    PITCH,
    STD_DEVIATION_OF_ELECTRON_CLOUD_FIT,
    STD_DEVIATION_OF_THE_NOISE,
    NUMBER_OF_ELECTRON_CLOUDS,
    strip_centers,
    x_coordinate_interpolate,
    charge_fraction_interpolate,
    electron_cloud_centers,
    SEED,
    THRESHOLD,
)

###############################################################################
#%% Plot of the errors of the position of the electron cloud center calculated by different methods
# to understand how this errors are calculated go to errors.py
##############################################################################
"""Errors of position reconstructions considering different positions of the electron cloud center
relative to the readout strips"""

labels = {
    "E_linear": "Linear weight",
    "E_quadratic": "Squared weight",
    "E_logarithmic": "Logarithmic weight",
    "Title": "Electron Cloud generated by Garfield++",
    "ylabel": "Errors",
}

labels_pt = {
    "E_linear": "Peso linear",
    "E_quadratic": "Peso quadrático",
    "E_logarithmic": "Peso logarítmico",
    "Title": "Nuvem de elétrons geradas pelo Garfield++",
    "ylabel": "Erros (mm)",
}

plot_errors(df, labels_pt)
