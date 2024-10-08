#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Name of script

Descriptin of script
This script allows the user to print to the console all columns in the
spreadsheet. It is assumed that the first row of the spreadsheet is the
location of the columns.

Input descripation. This tool accepts comma separated value files (.csv) as well as excel
(.xls, .xlsx) files.

Requirements. This script requires that `pandas` be installed within the Python
environment you are running this script in.

Function overview. This file can also be imported as a module and contains the following
functions:

    * get_spreadsheet_cols - returns the column headers of the file
    * main - the main function of the script
"""

# TODO
# add bit at bottom to turn this into actually executable script

import os

import numpy as np
import rasterio as rio

from calc_swe import *
from density_models import *


def extractYMD(dem_fn):
    """Extract YYYYMMDD from input dem fn.
    
    Parameters
    ----------
    dem_fn: str
        The file location of the input file
    
    Returns
    -------
    str
        the year, month and day as a concatenated string YYYYMMDD
    """

    from pathlib import PurePath
    YMD = PurePath(dem_fn).stem.split('_')[0]
    return YMD


def swe_models(h, YMD, sd_fn, bulk_density=0.3, snow_class="Alpine", outdir=None, 
               writeout=None, overwrite=False, verbose=None, dryrun=None):
    """Convert snow depth to snow water equivalent using the following models:
        
        bulk density:        
            assumes uniform density, default is 0.3 g/cm^3
        Sturm swe:           
            Sturm's 2010 empirical density model, default "Alpine" snow_class 
        Hill swe (paper):    
            Hill's empirical density model using data provided with paper        
        Hill swe (grid):     
            Hill's empirical density model using PRISM grids        
    
    Parameters
    ----------
    h: array
        [input m] 
    YMD: str
    sd_fn: str
    bulk_density: float
        
    outdir: str, optional
    writeout: bool, optional
    overwrite: bool, optional
    verbose: bool, optional
    dryrun: bool, optional

    Returns
    -------
    list, list
        swe_fns: a list of swe filenames as strings 
        swe_list: a list of arrays of calculated snow water equivalent [mm] 
        return order as bulk density, sturm, and hill (grid)
    
    indidivual models handle appropriate conversions
    Returns list of swe arrays in the following order: bulk density, sturm, and hill (grid)
    """
    
    # shorten snow depth filename input for swe filenaming and flexible swe outdir 
    short_sdfn = os.path.basename(sd_fn)

    # Specify default outdir 
    if outdir is None:
        outdir = os.path.dirname(sd_fn)
    
    swe_fns = []
    
    if verbose: print(f'Output directory is: \n{outdir}\n')
        
    ######## BULK SWE ########
    fn=f"{outdir}/{short_sdfn[:-7]}_bulk{int(bulk_density*1000)}SWE.tif"
    if verbose: print(f'Bulk SWE fn is: {fn}\n')
    if not dryrun:
        bulk_swe = bulkdensity_swecalc(h=h, bulk_density=bulk_density)
        # outputs in meters, convert to millimeters for consistency
        bulk_swe = bulk_swe*1000
        bulk_swe.name = 'Bulk SWE [mm]'
        if writeout: 
            write_out_rio(arr=bulk_swe, fn=fn, src_fn=sd_fn, 
                          overwrite=overwrite)
    swe_fns.append(fn)

    ######## STURM SWE ########
    fn = f"{outdir}/{short_sdfn[:-7]}_SturmSWE.tif"
    if verbose: print(f'Sturm SWE fn is: {fn}\n')
    if not dryrun:
        sturm_swe = sturm_swecalc(h=h, snow_class=snow_class, YMD=YMD)
        sturm_swe.name = 'Sturm SWE [mm]'
        if writeout: write_out_rio(arr=sturm_swe, fn=fn, src_fn=sd_fn, 
                                   overwrite=overwrite)
    swe_fns.append(fn)
    
    ######## HILL SWE ########
    # Convert snow depth from meters to millimeters
    fn = f"{outdir}/{short_sdfn[:-7]}_HillPaperSWE.tif"
    if verbose: print(f'Hill paper SWE fn is: {fn}\n')
    if not dryrun:
        sd_converted = get_snowdepth(arr=h, mm_convert=True)
        pptwt_fn = "/Users/jmhu/Downloads/tempnb_frompfe/data/ppt_wt_final.txt"
        td_fn = "/Users/jmhu/Downloads/tempnb_frompfe/data/td_final.txt"
        hill_swe_paper, _, _, _ = calc_swe(h=sd_converted, 
                                           td_fn=td_fn, pptwt_fn=pptwt_fn, 
                                           YMD=YMD)
        if writeout: write_out_rio(arr=hill_swe_paper, fn=fn, src_fn=sd_fn, 
                                   overwrite=overwrite)
    swe_fns.append(fn)
    
    fn = f"{outdir}/{short_sdfn[:-7]}_HillGridSWE.tif"
    if verbose: print(f'Hill grid SWE fn is: {fn}\n')
    if not dryrun:
        pptwt_fn = "/Users/jmhu/Downloads/tempnb_frompfe/data/PPTWT.tif"
        td_fn = "/Users/jmhu/Downloads/tempnb_frompfe/data/TD.tif"
        hill_swe, _, _, _ = calc_swe(h=sd_converted, 
                                     td_fn=td_fn, pptwt_fn=pptwt_fn, 
                                     YMD=YMD)
        if writeout: write_out_rio(arr=hill_swe, fn=fn, src_fn=sd_fn, 
                                   overwrite=overwrite)
    swe_fns.append(fn)
    
    if not dryrun: 
        swe_list = [bulk_swe, sturm_swe, hill_swe]
        return swe_fns, swe_list
    else:
        return swe_fns


def write_out_rio(arr, fn, src_fn=None, src=None, prof=None,
                  overwrite=False, dtype=rio.float32, bands=1, 
                  return_fns=False, dryrun=False):
    """Write raster to file using rasterio. Optionally overwrites existing file
    
    Parameters
    ----------
    arr: array
        The file location of the input file
    fn: array
        The file location of the input file
    src_fn: array
        The file location of the input file
    src: array
        The file location of the input file
    prof: array
        The file location of the input file
    overwrite: boolean, optional
        The file location of the input file
    dtype: rasterio datatype, default float32, optional 
        The file location of the input file
    bands: number of bands 
        The file location of the input file
    return_fns: boolean, optional
        The file location of the input file
    dryrun: boolean, optional
        The file location of the input file    
        
    Returns
    -------
    fn: str, optional
        output filename of written raster 
    """

    if not overwrite:
        if not os.path.exists(fn):
            print(f"\nDNE, writing {fn} to file...")
            if not dryrun:
                with rio.Env():
                    if src is not None: 
                        profile=src.profile
                    elif src_fn is not None: 
                        with rio.open(src_fn) as f: 
                            profile=f.profile
                    elif prof is not None:
                        profile=prof
                    with rio.open(fn, 'w', **profile) as dst:
                        dst.write(arr.astype(dtype), bands)
        else:
            print(f"\nFile already exists, \
                  toggle overwrite to True if you wish to overwrite: \n{fn}")
    else:
        print(f"\nFile exists, overwrite flag on, overwriting file \n{fn}")
        if not dryrun:
            with rio.Env():
                if src is not None: 
                    profile=src.profile
                elif src_fn is not None: 
                    with rio.open(src_fn) as f: 
                        profile=f.profile
                elif prof is not None:
                        profile=prof
                with rio.open(fn, 'w', **profile) as dst:
                    dst.write(arr.astype(dtype), bands)
    if return_fns:
        return fn
    print('Done')
