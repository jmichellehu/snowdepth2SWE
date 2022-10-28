#!/usr/bin/env python

import numpy as np
import os 
import rioxarray as rio

from density_models import *
from calc_swe import *

def write_out_rio(arr, fn, src_fn=None, src=None, overwrite=False, dtype=rio.float32, bands=1, return_fns=False, dryrun=False, prof=None):
    '''Write out raster dataset to file using rasterio, with option of overwriting existing file'''
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
            print(f"\nFile already exists, toggle overwrite to True if you wish to overwrite: \n{fn}")
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

def swe_models(h, YMD, sd_fn, bulk_density=0.3, snow_class="Alpine", outdir=None, 
               writeout=None, overwrite=False, verbose=None, dryrun=None):
    '''
    Converts snow depth [input m] to snow water equivalent [mm] using the following models:
        bulk density:        assumes uniform density, default is 0.3 g/cm^3, can be adjusted
        Sturm swe:           applies Sturm's 2010 empirical density model, employs default "Alpine" snow_class 
        Hill swe (paper):    Hill's empirical density model using data provided with paper        
        Hill swe (grid):     Hill's empirical density model using PRISM grids        
    
    indidivual models handle appropriate conversions
    Returns list of swe arrays in the following order: bulk density, hill (grid), and sturm
    '''
    # shorten snow depth filename input for swe filenaming and flexible swe outdir 
    short_sdfn=os.path.basename(sd_fn)

    # Specify default outdir 
    if outdir is None:
        outdir=os.path.dirname(sd_fn)
    
    swe_fns=[]
    
    if verbose: print(f'Output directory is: \n{outdir}\n')
        
    ######## BULK SWE ########
    fn=f"{outdir}/{short_sdfn[:-7]}_bulk{int(bulk_density*1000)}SWE.tif"
    if verbose: print(f'Bulk SWE fn is: {fn}\n')
    if not dryrun:
        bulk_swe = bulkdensity_swecalc(h=h, bulk_density=bulk_density)
        # outputs in meters, need to convert to mm... make sure that this makes sense
        bulk_swe=bulk_swe*1000
        bulk_swe.name='Bulk SWE [mm]'
        if writeout: write_out_rio(arr=bulk_swe, fn=fn, src_fn=sd_fn, overwrite=overwrite)
    swe_fns.append(fn)

    ######## STURM SWE ########
    fn=f"{outdir}/{short_sdfn[:-7]}_SturmSWE.tif"
    if verbose: print(f'Sturm SWE fn is: {fn}\n')
    if not dryrun:
        sturm_swe = sturm_swecalc(h=h, snow_class=snow_class, YMD=YMD)
        sturm_swe.name='Sturm SWE [mm]'
        if writeout: write_out_rio(arr=sturm_swe, fn=fn, src_fn=sd_fn, overwrite=overwrite)
    swe_fns.append(fn)
    
    ######## HILL SWE ########
    # Convert snow depth from meters to millimeters
    fn=f"{outdir}/{short_sdfn[:-7]}_HillPaperSWE.tif"
    if verbose: print(f'Hill paper SWE fn is: {fn}\n')
    if not dryrun:
        sd_converted=get_snowdepth(arr=h, mm_convert=True)
        pptwt_fn="data/ppt_wt_final.txt"
        td_fn="data/td_final.txt"
        hill_swe_paper, _, _, _ = calc_swe(h=sd_converted, td_fn=td_fn, pptwt_fn=pptwt_fn, YMD=YMD)
        if writeout: write_out_rio(arr=hill_swe_paper, fn=fn, src_fn=sd_fn, overwrite=overwrite)
    swe_fns.append(fn)
    
    fn=f"{outdir}/{short_sdfn[:-7]}_HillGridSWE.tif"
    if verbose: print(f'Hill grid SWE fn is: {fn}\n')
    if not dryrun:
        pptwt_fn="data/PPTWT.tif"
        td_fn="data/TD.tif"
        hill_swe, _, _, _ = calc_swe(h=sd_converted, td_fn=td_fn, pptwt_fn=pptwt_fn, YMD=YMD)
        if writeout: write_out_rio(arr=hill_swe, fn=fn, src_fn=sd_fn, overwrite=overwrite)
    swe_fns.append(fn)
    
    if not dryrun: 
        swe_list=[bulk_swe, hill_swe, sturm_swe]
        return swe_fns, swe_list
    else:
        return swe_fns