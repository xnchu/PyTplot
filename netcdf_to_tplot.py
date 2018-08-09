from netCDF4 import Dataset, num2date
import numpy as np
import pandas as pd
from pytplot import tplot, data_quants, store_data
import calendar


def change_time_to_unix_time(time_var):
    # A function that takes a variable with units of 'seconds/minutes/hours/etc. since YYYY-MM-DD:HH:MM:SS/etc
    # and converts the variable to seconds since epoch
    units = time_var.units
    dates = num2date(time_var[:], units=units)
    unix_times = list()
    for date in dates:
        unix_time = calendar.timegm(date.timetuple())
        unix_times.append(unix_time)
    return (unix_times)


def netcdf_to_tplot(filenames, prefix='', suffix='', plot=False, merge=False):
    '''
    This function will automatically create tplot variables from CDF files.

    Parameters:
        filenames : str/list of str
            The file names and full paths of netCDF files.
        prefix: str
            The tplot variable names will be given this prefix.  By default,
            no prefix is added.
        suffix: str
            The tplot variable names will be given this suffix.  By default,
            no suffix is added.
        plot: bool
            The data is plotted immediately after being generated.  All tplot
            variables generated from this function will be on the same plot.
            By default, a plot is not created.
        merge: bool
            If True, then data from different netCDF files will be merged into
            a single pytplot variable.

    Returns:
        List of tplot variables created.

    Examples:
        >>> #Create tplot variables from a GOES netCDF file
        >>> import pytplot
        >>> file = "/Users/user_name/goes_files/g15_epead_a16ew_1m_20171201_20171231.nc"
        >>> pytplot.netcdf_to_tplot(file, prefix='mvn_')

        >>> #Add a prefix, and plot immediately.
        >>> import pytplot
        >>> file = "/Users/user_name/goes_files/g15_epead_a16ew_1m_20171201_20171231.nc"
        >>> pytplot.netcdf_to_tplot(file, prefix='goes_prefix_', plot=True)

    '''

    stored_variables = []
    global data_quants

    print(data_quants)

    if isinstance(filenames, str):
        filenames = [filenames]
    elif isinstance(filenames, list):
        filenames = filenames
    else:
        print("Invalid filenames input.")
        #return stored_variables

    for filename in filenames:
        file = Dataset(filename, "r+")
        vars_and_atts = {} # Dictionary that will contain variables and their attributes (in case this info needs to be queried)
        for name, variable in file.variables.items():
            vars_and_atts[name] = {}
            for attrname in variable.ncattrs():
                vars_and_atts[name][attrname] = getattr(variable, attrname)

        masked_vars = {} # Dictionary containing properly masked variables
        for var in vars_and_atts.keys():
            # Grabbing each variable and replacing missing values with np.nan (if not already np.nan)
            reg_var = file.variables[var]
            try:
                var_fill_value = vars_and_atts[var]['missing_value']
                if np.isnan(var_fill_value) != True:
                    # We want to force missing values to be nan so that plots don't look strange
                    var_mask = np.ma.masked_where(reg_var==np.float32(var_fill_value),reg_var)
                    var_filled = np.ma.filled(var_mask,np.nan)
                elif np.isnan(var_fill_value) == True:
                    # missing values are already np.nan, don't need to do anything
                    var_filled = reg_var
            except: #continue # Go to next iteration, this variable doesn't have data to mask (probably just a descriptor variable (i.e., 'base_time')
                var_filled = reg_var
            masked_vars[var] = var_filled

        # Most files are from GOES data, which seems to usually have 'time_tag' in them that contain time information.
        # There is an exception filter below that will allow a user to pick a different time variable if time_tag doesn't exist.
        if 'time_tag' in vars_and_atts.keys():
            time_var = file['time_tag']
            unix_times = change_time_to_unix_time(time_var)

        if 'time_tag' not in vars_and_atts.keys():
            time_var_exists = input('Is there a differently-named time variable in the variables (y/n)? \nVariable list: {l}'.format(l=vars_and_atts.keys()))
            while True:
                if time_var_exists == 'y':
                    # Making sure we input a valid response (i.e., the variable exists in the dataset).
                    time = input('Great, now pick the time variable! \nPlease pick from {l}.'.format(l=vars_and_atts.keys()))
                    if time not in vars_and_atts.keys():
                        # Making sure we input a valid response (i.e., the variable exists in the dataset), and also avoiding
                        # plotting a time variable against time.... because I don't even know what that would mean and uncover.
                        print('Not a valid variable name, please try again.')
                        continue
                    elif time in vars_and_atts.keys():
                        # value is in the list of keys associated with this dataset, so we can go ahead and continue
                        time_var = time
                        unix_times = change_time_to_unix_time(time_var)
                        break
                elif time_var_exists != 'y' and time_var_exists != 'n':
                    print('You did not enter a valid response, please try again.')
                    # We grabbed whatever the time value is, yay! Time to grab the other variable to save/plot
                    continue
                elif time_var_exists == 'n':
                    print('Without a time variable, this file is not a valid file type for these kinds of plots.')
                    exit()

        while True:
            var_of_interest = input('What variable do you want to plot? Please pick from {l}.'.format(l=vars_and_atts.keys()))
            if var_of_interest not in vars_and_atts.keys() or 'time' in var_of_interest:
                # Making sure we input a valid response (i.e., the variable exists in the dataset), and also avoiding
                # plotting a time variable against time.... because I don't even know what that would mean.
                print('Not a valid variable, please try again.')
                continue
            else:
                # value is in the list of keys associated with this dataset, so we can go ahead and continue
                break

        # Store the data and then plot it up
        var_name = prefix + var + suffix
        to_merge = False
        if (var_name in data_quants.keys() and (merge==True)):
            prev_data_quant = data_quants[var_name].data
            print(prev_data_quant)
            to_merge = True

        tplot_data = {'x': unix_times, 'y': masked_vars[var_of_interest]}
        store_data(var_name, tplot_data)
        if var_name not in stored_variables:
            stored_variables.append(var_name)
        if to_merge == True:
            cur_data_quant = data_quants[var_name].data
            merged_data = [prev_data_quant, cur_data_quant]
            data_quants[var_name].data = pd.concat(merged_data)
    # If we are interested in seeing a quick plot of the variables, do it
    if plot:
        tplot(stored_variables)

    return(stored_variables)