#!/usr/bin/env python

import numpy as np

def grid_climate(ref, td_fn='TD.tif', pptwt_fn='PPTWT.tif'):
    '''Resamples, reprojects and clips extent of specified climate grids according to input reference raster.
        Input:
            ref: reference raster (e.g., snow depth)
            td_fn: temperature difference grid filename
            pptwt_fn: winter precipitation grid filename
    
        Returns:
            td [deg C]
                temperature difference grid
                
            pptwt [mm]
                winter precipitation grid
                
            TD_PPTWT_merge_proj [degrees C and mm]
                stack of regridded (projection, extent, resolution) temperature difference 
                and winter precipitation grids over area of interest       
    '''
    import rioxarray
    import xarray as xr
    from rasterio.enums import Resampling
    
    TD_fromdisk = rioxarray.open_rasterio(td_fn,
                                          masked=True,
                                          default_name='TD').squeeze(dim='band',
                                                                     drop=True)
    PPTWT_fromdisk = rioxarray.open_rasterio(pptwt_fn,
                                             masked=True,
                                             default_name='PPTWT').squeeze(dim='band',
                                                                           drop=True)

    TD_PPTWT_merge = xr.merge([TD_fromdisk, PPTWT_fromdisk])

    # Assign source crs
    TD_PPTWT_merge=TD_PPTWT_merge.rio.write_crs(4326)
    TD_PPTWT_merge.rio.crs
    
    TD_PPTWT_merge_proj = TD_PPTWT_merge.rio.reproject_match(ref, resampling=Resampling.cubic)

    td = TD_PPTWT_merge_proj['TD'].values
    pptwt = TD_PPTWT_merge_proj['PPTWT'].values

    return td, pptwt, TD_PPTWT_merge_proj

def get_snowdepth(ref_fn=None, arr=None, mm_convert=None):
    '''Loads snow depth array as rioxarray dataarray and converts to millimeters if needed
        Returns:
            h [mm]
                snow depth dataarray
    '''
    import rioxarray
    if ref_fn is not None:
        h = rioxarray.open_rasterio(ref_fn, masked=True, default_name='SD').squeeze(dim='band', drop=True)
    if arr is not None:
        h=arr
    if mm_convert is not None:
        # Convert from input units to millmeters. For meters, this value should be 1000
        h_new=h*1000
        return h_new
    else:
        return h

def calc_dowy(f):
    '''Calculates day of water year from string input of format "YYYYMMDD" .'''
    import datetime
    
    Y=int(f[:4])
    M=int(f[4:6])
    D=int(f[-2:])

    thisDate=datetime.date(Y, M, D)
    endDOWY=datetime.date(Y,9,30)
    diff = (endDOWY-thisDate).days

    # adjust for negative values
    if diff < 0:
        diff=diff+365

    # Calculate day of water year using this difference and numpy array functions
    DOWY = 365-diff

    # Comment out if you don't want leap year handling
    if (thisDate>datetime.date(Y, 2, 28)) & (thisDate <=endDOWY) & (Y%4) == 0:
        DOWY=DOWY+1

    return DOWY

def calc_swe(fn=None, h=None, YMD=None, mm_convert=None, 
             td_fn='TD.tif', pptwt_fn='PPTWT.tif', 
             a = (0.0533,0.9480,0.1701,-0.1314,0.2922),
             b = (0.0481,1.0395,0.1699,-0.0461,0.1804)
            ):
    '''Calculate SWE based on Hill et al. (2019) algorithm. Input snow depth raster filename or direct date input.
        Depth raster should be in [mm].
        
        Input
            fn: snow depth raster filename
            h: snow depth raster DataArray
            YMD: date string in YYYYMMDD format
            mm_convert: switch to convert snow depth from meters to millimeters
            td_fn: temperature difference grid filename
            pptwt_fn: winter precipitation grid fileanme
        
        Returns:
            swe [mm]
                calculated snow water equivalent raster
            
            h [mm]
                snow depth raster of area of interest
            
            TD_PPTWT_merge_proj [degrees C and mm]
                stack of regridded (projection, extent, resolution) temperature difference 
                and winter precipitation grids over area of interest
            
            DOWY
                day of water year (e.g. Oct. 1 ==> DOWY = 1)
    '''
    print("\nCalculating SWE...")
    if h is None:
        h=get_snowdepth(fn, mm_convert=mm_convert)
        
    td, pptwt, TD_PPTWT_merge_proj=grid_climate(h, td_fn, pptwt_fn)
    
    if YMD is not None:
        DOWY=calc_dowy(YMD)
    else:
        try: 
            DOWY=calc_dowy(fn.split("-")[1])
        except:
            print("Cannot find date in filename and no input date detected")
            exit(1)

    swe_calc = a[0]* h**a[1] * pptwt**a[2] * td**a[3] * DOWY**a[4]\
                * (-np.tanh(0.01*(DOWY-180))+1)/2 + b[0] * h**b[1] * pptwt**b[2]\
                * td**b[3] * DOWY**b[4] * (np.tanh(0.01 * (DOWY-180))+1)/2
    
    swe=h.copy()
    swe=swe.rename('SWE')    
    swe.values=swe_calc.values
    swe.attrs['default_name'] = 'SWE'
    swe.attrs['long_name'] = 'snow water equivalent [mm]'
    
    print(f"Mean Hill SWE is {np.mean(swe).values:.2f} millimeters")
    
    return swe, h, TD_PPTWT_merge_proj, DOWY

def write_SWE(in_fn, out_fn=None, YMD=None, mm_convert=None):
    '''Calculate SWE and write to file'''

#     swe, h, TD_PPTWT_merge_proj, DOWY = calc_swe(fn=in_fn, YMD=YMD)
    swe, _, _, DOWY = calc_swe(fn=in_fn, YMD=YMD, mm_convert=mm_convert)

    # Write it out
    print("\nWriting to file...")
    if out_fn is None:
        out_fn = "swe_DOWY" + str(DOWY) + ".tif"
    swe.rio.to_raster(out_fn, **kwargs)
    
