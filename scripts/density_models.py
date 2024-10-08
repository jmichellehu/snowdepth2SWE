#!/usr/bin/env python
import numpy as np

# Bulk density model based on climate classes of seasonal snow
# Sturm's model parameters by snow class - Table 4 in Sturm et al., 2010
# Ephemeral snow lacked sufficient systematic measurements, was excluded
# rho_max is the maximum bulk density of the season
# rho_init is the initial seasonal bulk density
# k1 is the densification parameter for snow_depth
# k2 is the densification parameter for DOY

def get_doy(f, handleleaps=True):
    """Calculates day of year from string input of format "YYYYMMDD" and has built-in leapyear handling
    Args:
        arg1
    
    Returns:
        Thing(s) that is/are returned.
    """
    
    import datetime
    Y = int(f[:4])
    M = int(f[4:6])
    D = int(f[-2:])
    
    thisDate = datetime.date(Y, M, D)
    yearEnd = datetime.date(Y,12,31)
    diff = (yearEnd-thisDate).days

    # Calculate day of water year using this difference and numpy array functions
    DOY = 365-diff

    # Leap year handling
    if handleleaps:
        if (thisDate>datetime.date(Y, 2, 28)) & (thisDate <= yearEnd) & (Y%4) == 0:
            DOY = DOY+1

    return DOY

def extract_byclass(c, snow_classes=("Alpine", "Maritime", "Prairie", "Tundra", "Taiga"),
                    rho_maxes = (0.5975, 0.5979, 0.5940, 0.3630, 0.2170),
                    rho_inits = (0.2237, 0.2578, 0.2332, 0.2425, 0.2170),
                    k1s = (0.0012, 0.0010, 0.0016, 0.0029, 0.0000),
                    k2s = (0.0038, 0.0038, 0.0031, 0.0049, 0.0000)):
    
    """Selects appropriate parameters based on string input snow climate class
    Args:
        arg1
    
    Returns:
        snow_class, rho_max, rho_init, k1, and k2
    """
    
    import sys
    
    if c in snow_classes:
        idx = snow_classes.index(c)
    elif c.title() in snow_classes:
        idx = snow_classes.index(c.title())
    else:
        sys.exit(f'Neither {c}, nor {c.title()} in {snow_classes}')
        
    return snow_classes[idx], rho_maxes[idx], rho_inits[idx], k1s[idx], k2s[idx]

def sturm_swecalc(h, snow_class, DOY=None, YMD=None, return_all=None):
    """Uses Sturm snow climate classes to derive SWE estimates, note input snow depth MUST be converted to centimeters. 
    Args:
        arg1
        Please input meters. 
    
    Returns:
        Thing(s) that is/are returned.
        Returned swe will be in centimeters
    """
    import numpy as np
    if DOY is None:
        DOY = get_doy(YMD)
    
    returnedsnow_class, rho_max, rho_init, k1, k2=extract_byclass(c=snow_class)
    
    h_cm = h*10 # convert from meters to centimeters 
    rho_b_model = (rho_max - rho_init) * (1-np.exp(-k1 * h_cm - k2 * DOY)) + rho_init
    
    # Convert to millimeters of SWE
    swe = np.multiply(rho_b_model, h) * 1000
    if type(swe) == np.ma.core.MaskedArray:
        print(f'Mean Sturm SWE using sturm bulk density of {np.nanmean(rho_b_model):.2f} gcm-3 is {np.nanmean(swe):.2f} mm ')
    else:
        print(f'Mean Sturm SWE using sturm bulk density of {np.nanmean(rho_b_model.values):.2f} gcm-3 is {np.nanmean(swe.values):.2f} mm ')
    if return_all:
        return swe, rho_b_model, returnedsnow_class, rho_max, rho_init, k1, k2, DOY  
    else:
        return swe

def bulkdensity_swecalc(h, bulk_density):
    import numpy as np
    """Basic SWE calculation using snow depth and input bulk density, depth in meters and bulk_density in kg/m^3"""
    """Docstring short description
    
    Args:
        arg1
    
    Returns:
        Thing(s) that is/are returned.
    Need better handling for input array type MaskedArray or DataArray
    """
    swe = h * bulk_density
    if type(swe) == np.ma.core.MaskedArray:
        print(f"SWE from basic calculations using bulk density of {bulk_density} gcm-3 is {np.nanmean(swe):.2f} meters")
    else:
        print(f"SWE from basic calculations using bulk density of {bulk_density} gcm-3 is {np.nanmean(swe.values):.2f} meters")
    return swe

def get_sturm_density():
    """Docstring short description
    
    Args:
        arg1
    
    Returns:
        Thing(s) that is/are returned.
    """

    snow_classes = ["Alpine", "Maritime", "Prairie", "Tundra", "Taiga"]
    rho_maxes = [0.5975, 0.5979, 0.5940, 0.3630, 0.2170]
    rho_inits = [0.2237, 0.2578, 0.2332, 0.2425, 0.2170]
    k1s = [0.0012, 0.0010, 0.0016, 0.0029, 0.0000]
    k2s = [0.0038, 0.0038, 0.0031, 0.0049, 0.0000]

    # Will need to extract day of year, pre-existing snow depth, and climate class based on image metadata (location, date of collection, etc.)
    DOY_i = -92          # specify the day of year of interest (-92 = Oct 1; +181 = June 30)
    h_i = 1.4           # ith observation of snow_depth in meters

    climate_class = 0   # values range 0-4 based on snow class

    snow_class = snow_classes[climate_class]
    rho_max = rho_maxes[climate_class]
    rho_init = rho_inits[climate_class]
    k1 = k1s[climate_class]
    k2 = k2s[climate_class]

    # t = snow deposition history
    # rho_b = function of h_s, t, and initial snow layer density
    rho_b_model = (rho_max - rho_init) * (1-np.exp(-k1 * h_i - k2 * DOY_i)) + rho_init
    # print(rho_b_model)
    return rho_b_model

    # Basic SWE calculation using snow_depth and bulk_density
    # h_s = 1             # snow_depth in meters
    # rho_w = 1           # density_of_water in grams/cubic cm
    # rho_b = 0.3         # bulk_density in grams/cubic cm

    # swe = h_s * rho_b_model / rho_w
    # print("SWE from basic calculations using bulk density based on snow class is "
    # + str(format(swe, '.2f')) + " meters in the " + snow_class + " snow class.")
