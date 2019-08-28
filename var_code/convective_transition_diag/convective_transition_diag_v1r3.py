# This file is part of the convective_transition_diag module of the MDTF code package (see mdtf/MDTF_v2.0/LICENSE.txt)

# ======================================================================
# convective_transition_diag_v1r3.py
#
#   Convective Transition Diagnostic Package
#   
#   The convective transition diagnostic package computes statistics that relate 
#    precipitation to measures of tropospheric temperature and moisture, as an evaluation 
#    of the interaction of parameterized convective processes with the large-scale 
#    environment. Here the basic statistics include the conditional average and 
#    probability of precipitation, PDF of column water vapor (CWV) for all events and 
#    precipitating events, evaluated over tropical oceans. The critical values at which 
#    the conditionally averaged precipitation sharply increases as CWV exceeds the 
#    critical threshold are also computed (provided the model exhibits such an increase).
#
#   Version 1 revision 3 13-Nov-2017 Yi-Hung Kuo (UCLA)
#   PI: J. David Neelin (UCLA; neelin@atmos.ucla.edu)
#   Current developer: Yi-Hung Kuo (yhkuo@atmos.ucla.edu)
#   Contributors: K. A. Schiro (UCLA), B. Langenbrunner (UCLA), F. Ahmed (UCLA),
#    C. Martinez (UCLA), C.-C. (Jack) Chen (NCAR)
#
#   This package and the MDTF code package are distributed under the LGPLv3 license 
#    (see LICENSE.txt).
#
#   Currently consists of following functionalities:
#    (1) Convective Transition Basic Statistics (convecTransBasic.py)
#    (2) Convective Transition Critical Collapse (convecTransCriticalCollapse.py)
#    *(3) Moisture Precipitation Joint Probability Density Function (cwvPrecipJPDF.py)
#    *(4) Super Critical Precipitation Probability (supCriticPrecipProb.py)
#    More on the way...(* under development)
#
#   As a module of the MDTF code package, all scripts of this package can be found under
#    mdtf/MDTF_$ver/var_code/convective_transition_diag**
#   and pre-digested observational data under 
#    mdtf/inputdata/obs_data/convective_transition_diag
#   (**$ver depends on the actual version of the MDTF code package)
#
#   This package is written in Python 2, and requires the following Python packages:
#    os,glob,json,Dataset,numpy,scipy,matplotlib, networkx,warnings,numba, netcdf4
#   The plotting functions in this package depend on an older version of matplotlib, 
#    thus an older version of the Anaconda 2 installer (ver. 5.0.1) is recommended
#
#   The following three 3-D (lat-lon-time) high-frequency model fields are required:
#     (1) precipitation rate (units: mm/s = kg/m^2/s; 6-hrly avg. or shorter)
#     (2) column water vapor (CWV, or precipitable water vapor; units: mm = kg/m^2)
#     (3) column-integrated saturation humidity (units: mm = kg/m^2)
#          or mass-weighted column average temperature (units: K) 
#          with column being 1000-200 hPa by default 
#   Since (3) is not standard model output, this package will automatically
#    calculate (3) if the following 4-D (lat-lon-pressure-time) model field is available:
#     (4) air temperature (units: K)
#
#   Reference: 
#    Kuo, Y.-H., K. A. Schiro, and J. D. Neelin, 2018: Convective transition statistics 
#      over tropical oceans for climate model diagnostics: Observational baseline. 
#      J. Atmos. Sci., 75, 1553-1570.
#    Kuo, Y.-H., and Coauthors: Convective transition statistics over tropical oceans
#      for climate model diagnostics: GCM performance. In preparation.***
#    ***See http://research.atmos.ucla.edu/csi//REF/pub.html for updates.
# ======================================================================
# Import standard Python packages
import os
import glob


os.environ["pr_file"] = "*."+os.environ["pr_var"]+".1hr.nc"
os.environ["prw_file"] = "*."+os.environ["prw_var"]+".1hr.nc"
os.environ["ta_file"] = "*."+os.environ["ta_var"]+".1hr.nc"
os.environ["tave_file"] = "*."+os.environ["tave_var"]+".1hr.nc"
os.environ["qsat_int_file"] = "*."+os.environ["qsat_int_var"]+".1hr.nc"

## Model output filename convention
os.environ["MODEL_OUTPUT_DIR"]=os.environ["DATADIR"]+"/1hr"
#os.environ["pr_file"] = "*."+os.environ["pr_var"]+".1hr.nc"
#os.environ["prw_file"] = "*."+os.environ["prw_var"]+".1hr.nc"
#os.environ["ta_file"] = "*."+os.environ["ta_var"]+".1hr.nc"
#os.environ["tave_file"] = "*."+os.environ["tave_var"]+".1hr.nc"
#os.environ["qsat_int_file"] = "*."+os.environ["qsat_int_var"]+".1hr.nc"

# Specify parameters for Convective Transition Diagnostic Package
# Use 1:tave, or 2:qsat_int as Bulk Tropospheric Temperature Measure 
os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] = "2"
os.environ["RES"] = "1.00" # Spatial Resolution (degree) for TMI Data (0.25, 0.50, 1.00)

missing_file=0
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["pr_file"]))==0:
    print("Required Precipitation data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["prw_file"]))==0:
    print("Required Precipitable Water Vapor (CWV) data missing!")
    missing_file=1
if len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["ta_file"]))==0:
    if (os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"]=="2" and \
       len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["qsat_int_file"]))==0) \
    or (os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"]=="1" and \
       (len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["qsat_int_file"]))==0 or \
        len(glob.glob(os.environ["MODEL_OUTPUT_DIR"]+"/"+os.environ["tave_file"]))==0)):
        print("Required Temperature data missing!")
        missing_file=1

if missing_file==1:
    print("Convective Transition Diagnostic Package will NOT be executed!")
else:
    # ======================================================================
    # Create directories
    # ======================================================================
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/model"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/model")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/model/netCDF"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/model/netCDF")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/model/PS"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/model/PS")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/obs"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/obs")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/obs/PS"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/obs/PS")
    if not os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/obs/netCDF"):
        os.makedirs(os.environ["variab_dir"]+"/convective_transition_diag/obs/netCDF")

    ##### Functionalities in Convective Transition Diagnostic Package #####
    # ======================================================================
    # Convective Transition Basic Statistics
    #  See convecTransBasic.py for detailed info
    try:
        os.system("python "+os.environ["VARCODE"]+"/convective_transition_diag/"+"convecTransBasic.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Convective Transition Basic Statistics (convecTransBasic.py) is NOT Executed as Expected!")		
        print("**************************************************")

    ## ======================================================================
    ## Convective Transition Critical Collapse
    ##  Requires output from convecTransBasic.py
    ##  See convecTransCriticalCollapse.py for detailed info
    try:
        os.system("python "+os.environ["VARCODE"]+"/convective_transition_diag/"+"convecTransCriticalCollapse.py")
    except OSError as e:
        print('WARNING',e.errno,e.strerror)
        print("**************************************************")
        print("Convective Transition Thermodynamic Critical Collapse (convecTransCriticalCollapse.py) is NOT Executed as Expected!")		
        print("**************************************************")

    ##### THE FOLLOWING FUNCTIONALITIES HAVE NOT BEEN IMPLEMENTED YET!!!#####
    ## ======================================================================
    ## Moisture Precipitation Joint Probability Density Function
    ##  See cwvPrecipJPDF.py for detailed info
    #os.system("python "+os.environ["VARCODE"]+"/convective_transition_diag/"+"cwvPrecipJPDF.py")
    ## ======================================================================
    ## Super Critical Precipitation Probability
    ##  Requires output from convecTransBasic.py
    ##  See supCriticPrecipProb.py for detailed info
    #os.system("python "+os.environ["VARCODE"]+"/convective_transition_diag/"+"supCriticPrecipProb.py")

    ######################### HTML sections below #########################
    # ======================================================================
    #  Copy & modify the template html
    # ======================================================================
    # Copy template html (and delete old html if necessary)
    if os.path.isfile( os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html" ):
        os.system("rm -f "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")

    os.system("cp "+os.environ["VARCODE"]+"/convective_transition_diag/convective_transition_diag.html "+os.environ["variab_dir"]+"/convective_transition_diag/.")

    os.system("cp "+os.environ["VARCODE"]+"/convective_transition_diag/MDTF_Documentation_convective_transition.pdf "+os.environ["variab_dir"]+"/convective_transition_diag/.")

    # Replace keywords in the copied html template if different bulk temperature or resolution are used
    if os.environ["BULK_TROPOSPHERIC_TEMPERATURE_MEASURE"] == "2":
        os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/_tave\./_qsat_int\./g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
        os.system("mv "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")
    if os.environ["RES"] != "1.00":
        os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/_res\=1\.00_/_res\="+os.environ["RES"]+"_/g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
        os.system("mv "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")

    # Replace CASENAME so that the figures are correctly linked through the html
    os.system("cp "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
    os.system("cat "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html "+"| sed -e s/casename/"+os.environ["CASENAME"]+"/g > "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")
    os.system("cp "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html "+os.environ["variab_dir"]+"/convective_transition_diag/convective_transition_diag.html")
    os.system("rm -f "+os.environ["variab_dir"]+"/convective_transition_diag/tmp.html")

    a = os.system("cat "+os.environ["variab_dir"]+"/index.html | grep convective_transition_diag")
    if a != 0:
       os.system("echo '<H3><font color=navy>Convective transition diagnostics <A HREF=\"convective_transition_diag/convective_transition_diag.html\">plots</A></H3>' >> "+os.environ["variab_dir"]+"/index.html")

    # Convert PS to png
    if os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/model"):
        files = os.listdir(os.environ["variab_dir"]+"/convective_transition_diag/model/PS")
        a = 0
        while a < len(files):
            file1 = os.environ["variab_dir"]+"/convective_transition_diag/model/PS/"+files[a]
            file2 = os.environ["variab_dir"]+"/convective_transition_diag/model/"+files[a]
            os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
            a = a+1
        if os.environ["save_ps"] == "0":
            os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/model/PS")
    if os.path.exists(os.environ["variab_dir"]+"/convective_transition_diag/obs"):
        files = os.listdir(os.environ["variab_dir"]+"/convective_transition_diag/obs/PS")
        a = 0
        while a < len(files):
            file1 = os.environ["variab_dir"]+"/convective_transition_diag/obs/PS/"+files[a]
            file2 = os.environ["variab_dir"]+"/convective_transition_diag/obs/"+files[a]
            os.system("convert -crop 0x0+5+5 "+file1+" "+file2[:-3]+".png")
            a = a+1
        if os.environ["save_ps"] == "0":
            os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/obs/PS")

    # delete netCDF files if requested
    if os.environ["save_nc"] == "0":    
        os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/obs/netCDF")
        os.system("rm -rf "+os.environ["variab_dir"]+"/convective_transition_diag/model/netCDF")

    # ======================================================================
    # End of HTML sections
    # ======================================================================    

    print("**************************************************")
    print("Convective Transition Diagnostic Package (convective_transition_diag_v1r3.py) Executed!")
    print("**************************************************")
