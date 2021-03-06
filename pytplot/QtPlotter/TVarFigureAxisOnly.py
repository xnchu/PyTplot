# Copyright 2018 Regents of the University of Colorado. All Rights Reserved.
# Released under the MIT license.
# This software was developed at the University of Colorado's Laboratory for Atmospheric and Space Physics.
# Verify current version before use at: https://github.com/MAVENSDC/PyTplot

import pyqtgraph as pg
from scipy import interpolate
from .CustomAxis.NonLinearAxis import NonLinearAxis
from .CustomViewBox.CustomVB import CustomVB
import pytplot


class TVarFigureAxisOnly(pg.GraphicsLayout):
    def __init__(self, tvar_name):
        self.tvar_name = tvar_name
        
        # Sets up the layout of the Tplot Object
        pg.GraphicsLayout.__init__(self)
        self.layout.setHorizontalSpacing(50)
        self.layout.setContentsMargins(0, 0, 0, 0)

        if pytplot.tplot_opt_glob['black_background']:
            self.labelStyle = {'font-size':
                               str(pytplot.data_quants[self.tvar_name].attrs['plot_options']['extras']['char_size'])
                               + 'pt', 'color': '#FFF'}
        else:
            self.labelStyle = {'font-size':
                               str(pytplot.data_quants[self.tvar_name].attrs['plot_options']['extras']['char_size'])
                               + 'pt', 'color': '#000'}
        
        vb = CustomVB(enableMouse=False)
        yaxis = pg.AxisItem("left")
        yaxis.setLabel(pytplot.data_quants[self.tvar_name].attrs['plot_options']['yaxis_opt']['axis_label'], **self.labelStyle)
        yaxis.setWidth(100)
        yaxis.label.rotate(90)
        yaxis.label.translate(0, -40)
        mapping_function = interpolate.interp1d(pytplot.data_quants[self.tvar_name].coords['time'].values, pytplot.data_quants[self.tvar_name].values)
        xaxis = NonLinearAxis(orientation='bottom', mapping_function=mapping_function)
        self.plotwindow = self.addPlot(row=0, col=0, axisItems={'bottom': xaxis, 'left': yaxis}, viewBox=vb, colspan=1)
        self.plotwindow.buttonsHidden = True
        self.plotwindow.setMaximumHeight(20)
        
        # Set up the view box needed for the legends
        self.legendvb = pg.ViewBox(enableMouse=False)
        self.legendvb.setMaximumWidth(100)
        self.addItem(self.legendvb, 0, 1)
