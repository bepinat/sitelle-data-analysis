import os
import sys
import time
import traceback
import inspect
import re
import datetime
import logging
import warnings

import threading
import socketserver
import logging.handlers
import struct
import pickle
import select
import socket

import numpy as np
import astropy.io.fits as pyfits
import astropy.wcs as pywcs
from scipy import interpolate

try: import pygit2
except ImportError: pass

## MODULES IMPORTS
import orb.utils.spectrum
import orb.utils.parallel
import orb.utils.io
import orb.utils.filters
import orb.utils.photometry
from orb.core import ProgressBar
import orb.core
    


##################################################
#### CLASS Cube ##################################
##################################################
class Cube(orb.core.Tools):
    """3d numpy data cube handling. Base class for all Cube classes"""
    def __init__(self, data, **kwargs):
        """
        Initialize Cube class.

        :param data: Can be a path to a FITS file containing a data
          cube or a 3d numpy.ndarray. Can be None if data init is
          handled differently (e.g. if this class is inherited)

        :param kwargs: (Optional) :py:class:`~orb.core.Tools` kwargs.
        """
        orb.core.Tools.__init__(self, **kwargs)

        self.star_list = None
        self.z_median = None
        self.z_mean = None
        self.z_std = None
        self.mean_image = None
        self._silent_load = False

        self._return_mask = False # When True, __get_item__ return mask data
                                  # instead of 'normal' data

        # read directives
        self.is_hdf5_frames = None # frames are hdf5 frames (i.e. the cube is
                                   # not an HDF5 cube but is made from
                                   # hdf5 frames)
        self.is_hdf5_cube = None # tell if the cube is an hdf5 cube
                                 # (i.e. created via OutHDFCube or
                                 # OutHDFQuadCube)
        self.is_quad_cube = False # Basic cube is not quad cube (see
                                  # class HDFCube and OutHDFQuadCube)


        self.is_complex = False
        self.dtype = float
        
        if data is None: return
        
        # check data
        if isinstance(data, str):
            data = orb.utils.io.read_fits(data)

        orb.utils.validate.is_3darray(data)
        orb.utils.validate.has_dtype(data, float)
        
        self._data = np.copy(data)
        self.dimx = self._data.shape[0]
        self.dimy = self._data.shape[1]
        self.dimz = self._data.shape[2]
        self.shape = (self.dimx, self.dimy, self.dimz)

    def __getitem__(self, key):
        """Getitem special method"""
        return self._data.__getitem__(key)

    def _get_default_slice(self, _slice, _max):
        """Utility function used by __getitem__. Return a valid slice
        object given an integer or slice.

        :param _slice: a slice object or an integer
        :param _max: size of the considered axis of the slice.
        """
        if isinstance(_slice, slice):
            if _slice.start is not None:
                if (isinstance(_slice.start, int)
                    or isinstance(_slice.start, int)):
                    if (_slice.start >= 0) and (_slice.start <= _max):
                        slice_min = int(_slice.start)
                    else:
                        raise Exception(
                            "Index error: list index out of range")
                else:
                    raise Exception("Type error: list indices of slice must be integers")
            else: slice_min = 0

            if _slice.stop is not None:
                if (isinstance(_slice.stop, int)
                    or isinstance(_slice.stop, int)):
                    if _slice.stop < 0: # transform negative index to real index
                        slice_stop = _max + _slice.stop
                    else:  slice_stop = _slice.stop
                    if ((slice_stop <= _max)
                        and slice_stop > slice_min):
                        slice_max = int(slice_stop)
                    else:
                        raise Exception(
                            "Index error: list index out of range")

                else:
                    raise Exception("Type error: list indices of slice must be integers")
            else: slice_max = _max

        elif isinstance(_slice, int) or isinstance(_slice, int):
            slice_min = _slice
            slice_max = slice_min + 1
        else:
            raise Exception("Type error: list indices must be integers or slices")
        return slice(slice_min, slice_max, 1)


    def _get_hdf5_data_path(self, frame_index, mask=False):
        """Return path to the data of a given frame in an HDF5 cube.

        :param frame_index: Index of the frame
        
        :param mask: (Optional) If True, path to the masked frame is
          returned (default False).
        """
        if mask: return self._get_hdf5_frame_path(frame_index) + '/mask'
        else: return self._get_hdf5_frame_path(frame_index) + '/data'

    def _get_hdf5_quad_data_path(self, quad_index):
        """Return path to the data of a given quad in an HDF5 cube.

        :param quad_index: Index of the quadrant
        """
        return self._get_hdf5_quad_path(quad_index) + '/data'
        

    def _get_hdf5_header_path(self, frame_index):
        """Return path to the header of a given frame in an HDF5 cube.

        :param frame_index: Index of the frame
        """
        return self._get_hdf5_frame_path(frame_index) + '/header'

    def _get_hdf5_quad_header_path(self, quad_index):
        """Return path to the header of a given quadrant in an HDF5 cube.

        :param frame_index: Index of the quadrant
        """
        return self._get_hdf5_quad_path(quad_index) + '/header'

    def _get_hdf5_frame_path(self, frame_index):
        """Return path to a given frame in an HDF5 cube.

        :param frame_index: Index of the frame.
        """
        return 'frame{:05d}'.format(frame_index)

    
    def _get_hdf5_quad_path(self, quad_index):
        """Return path to a given quadrant in an HDF5 cube.

        :param quad_index: Index of the quad.
        """
        return 'quad{:03d}'.format(quad_index)

    def get_data(self, x_min, x_max, y_min, y_max,
                 z_min, z_max, silent=False, mask=False):
        """Return a part of the data cube.

        :param x_min: minimum index along x axis
        
        :param x_max: maximum index along x axis
        
        :param y_min: minimum index along y axis
        
        :param y_max: maximum index along y axis
        
        :param z_min: minimum index along z axis
        
        :param z_max: maximum index along z axis
        
        :param silent: (Optional) if False display a progress bar
          during data loading (default False)

        :param mask: (Optional) if True return mask (default False).
        """
        if silent:
            self._silent_load = True
        if mask:
            self._return_mask = True
        data = self[int(x_min):int(x_max), int(y_min):int(y_max), int(z_min):int(z_max)]
        self._silent_load = False
        self._return_mask = False
        return data
        
    def get_mean_image(self, recompute=False):
        """Return the mean image of a cube (corresponding to a deep
        frame for an interferogram cube or a specral cube).

        :param recompute: (Optional) Force to recompute mean image
          even if it is already present in the cube (default False).
        
        .. note:: In this process NaNs are considered as zeros.
        """
        if self.mean_image is None or recompute:
            mean_im = np.zeros((self.dimx, self.dimy), dtype=self.dtype)
            progress = ProgressBar(self.dimz)
            for _ik in range(self.dimz):
                frame = self[:,:,_ik]
                non_nans = np.nonzero(~np.isnan(frame))
                mean_im[non_nans] += frame[non_nans]
                progress.update(_ik, info="Creating mean image")
            progress.end()
            self.mean_image = mean_im / self.dimz
        return self.mean_image            
            




#################################################
#### CLASS HDFCube ##############################
#################################################


class HDFCube(Cube):
    """ This class implements the use of an HDF5 cube.

    An HDF5 cube is similar to the *frame-divided cube* implemented by
    the class :py:class:`orb.core.Cube` but it makes use of the really
    fast data access provided by HDF5 files. The "frame-divided"
    concept is keeped but all the frames are grouped into one hdf5
    file.

    An HDF5 cube must have a certain architecture:
    
    * Each frame has its own group called 'frameIIIII', IIIII being a
      integer giving the position of the frame on 5 characters filled
      with zeros. e.g. the first frame group is called frame00000

    * Each frame group is divided into at least 2 datasets: **data**
      and *header* (e.g. the data of the first frame will be in the
      dataset *frame00000/data*)

    * A **mask** dataset can be added to each frame.
    """        
    def __init__(self, cube_path, params=None,
                 silent_init=False,
                 binning=None, **kwargs):
        
        """
        Initialize HDFCube class.
        
        :param cube_path: Path to the HDF5 cube.

        :param params: Path to an option file or dictionary containtin
          observation parameters.

        :param overwrite: (Optional) If True existing FITS files will
          be overwritten (default True).

        :param indexer: (Optional) Must be a :py:class:`core.Indexer`
          instance. If not None created files can be indexed by this
          instance.

        :param binning: (Optional) Cube binning. If > 1 data will be
          transparently binned so that the cube will behave as as if
          it was already binned (default None).

        :param silent_init: (Optional) If True Init is silent (default False).

        :param kwargs: Kwargs are :py:class:`~core.Tools` properties.
        """
        Cube.__init__(self, None, **kwargs)
            
        self._hdf5f = None # Instance of h5py.File
        self.quad_nb = None # number of quads (set to None if HDFCube
                            # is not a cube split in quads but a cube
                            # split in frames)
        self.is_quad_cube = None # set to True if cube is split in quad. set to
                                 # False if split in frames.

        
        self.is_hdf5_cube = True
        self.is_hdf5_frames = False
        self.image_list = None
        self._prebinning = None
        if binning is not None:
            if int(binning) > 1:
                self._prebinning = int(binning)
            
        self._parallel_access_to_data = False

        if cube_path is None or cube_path == '': return
        
        with orb.utils.io.open_hdf5(cube_path, 'r') as f:
            self.cube_path = cube_path
            self.dimz = self._get_attribute('dimz')
            self.dimx = self._get_attribute('dimx')
            self.dimy = self._get_attribute('dimy')
            if 'image_list' in f:
                self.image_list = f['image_list'][:]
            
            # check if cube is quad or frames based
            self.quad_nb = self._get_attribute('quad_nb', optional=True)
            if self.quad_nb is not None:
                self.is_quad_cube = True
            else:
                self.is_quad_cube = False
        
            # sanity check
            if self.is_quad_cube:
                quad_nb = len(
                    [igrp for igrp in f
                     if 'quad' == igrp[:4]])
                if quad_nb != self.quad_nb:
                    raise Exception("Corrupted HDF5 cube: 'quad_nb' attribute ([]) does not correspond to the real number of quads ({})".format(self.quad_nb, quad_nb))

                if self._get_hdf5_quad_path(0) in f:
                    # test whether data is complex
                    if np.iscomplexobj(f[self._get_hdf5_quad_data_path(0)]):
                        self.is_complex = True
                        self.dtype = complex
                    else:
                        self.is_complex = False
                        self.dtype = float
                
                else:
                    raise Exception('{} is missing. A valid HDF5 cube must contain at least one quadrant'.format(
                        self._get_hdf5_quad_path(0)))
                    

            else:
                frame_nb = len(
                    [igrp for igrp in f
                     if 'frame' == igrp[:5]])

                if frame_nb != self.dimz:
                    raise Exception("Corrupted HDF5 cube: 'dimz' attribute ({}) does not correspond to the real number of frames ({})".format(self.dimz, frame_nb))
                
            
                if self._get_hdf5_frame_path(0) in f:                
                    if ((self.dimx, self.dimy)
                        != f[self._get_hdf5_data_path(0)].shape):
                        raise Exception('Corrupted HDF5 cube: frame shape {} does not correspond to the attributes of the file {}x{}'.format(f[self._get_hdf5_data_path(0)].shape, self.dimx, self.dimy))

                    if self._get_hdf5_data_path(0, mask=True) in f:
                        self._mask_exists = True
                    else:
                        self._mask_exists = False

                    # test whether data is complex
                    if np.iscomplexobj(f[self._get_hdf5_data_path(0)]):
                        self.is_complex = True
                        self.dtype = complex
                    else:
                        self.is_complex = False
                        self.dtype = float
                else:
                    raise Exception('{} is missing. A valid HDF5 cube must contain at least one frame'.format(
                        self._get_hdf5_frame_path(0)))
                

        # binning
        if self._prebinning is not None:
            self.dimx = self.dimx / self._prebinning
            self.dimy = self.dimy / self._prebinning

        if (self.dimx) and (self.dimy) and (self.dimz):
            if not silent_init:
                logging.info("Data shape : (" + str(self.dimx) 
                                + ", " + str(self.dimy) + ", " 
                                + str(self.dimz) + ")")
        else:
            raise Exception("Incorrect data shape : (" 
                            + str(self.dimx) + ", " + str(self.dimy) 
                              + ", " +str(self.dimz) + ")")

        self.shape = (self.dimx, self.dimy, self.dimz)

        if params is not None:
            self.compute_data_parameters()

        
    def __getitem__(self, key):
        """Implement the evaluation of self[key].
        
        .. note:: To make this function silent just set
          Cube()._silent_load to True.
        """
        def slice_in_quad(ax_slice, ax_min, ax_max):
            ax_range = list(range(ax_min, ax_max))
            for ii in range(ax_slice.start, ax_slice.stop):
                if ii in ax_range:
                    return True
            return False
        # check return mask possibility
        if self._return_mask and not self._mask_exists:
            raise Exception("No mask found with data, cannot return mask")
        
        # produce default values for slices
        x_slice = self._get_default_slice(key[0], self.dimx)
        y_slice = self._get_default_slice(key[1], self.dimy)
        z_slice = self._get_default_slice(key[2], self.dimz)

        data = np.empty((x_slice.stop - x_slice.start,
                         y_slice.stop - y_slice.start,
                         z_slice.stop - z_slice.start), dtype=self.dtype)

        if self._prebinning is not None:
            x_slice = slice(x_slice.start * self._prebinning,
                            x_slice.stop * self._prebinning, 1)
            y_slice = slice(y_slice.start * self._prebinning,
                            y_slice.stop * self._prebinning, 1)

        # frame based cube
        if not self.is_quad_cube:

            if z_slice.stop - z_slice.start == 1:
                only_one_frame = True
            else:
                only_one_frame = False

            with orb.utils.io.open_hdf5(self.cube_path, 'r') as f:
                if not self._silent_load and not only_one_frame:
                    progress = ProgressBar(z_slice.stop - z_slice.start - 1)

                for ik in range(z_slice.start, z_slice.stop):
                    unbin_data = f[
                        self._get_hdf5_data_path(
                            ik, mask=self._return_mask)][x_slice, y_slice]

                    if self._prebinning is not None:
                        data[0:x_slice.stop - x_slice.start,
                             0:y_slice.stop - y_slice.start,
                             ik - z_slice.start] = orb.utils.image.nanbin_image(
                            unbin_data, self._prebinning)
                    else:
                        data[0:x_slice.stop - x_slice.start,
                             0:y_slice.stop - y_slice.start,
                             ik - z_slice.start] = unbin_data

                    if not self._silent_load and not only_one_frame:
                        if not ik%100:
                            progress.update(ik - z_slice.start, info="Loading data")

                if not self._silent_load and not only_one_frame:
                    progress.end()

        # quad based cube
        else:
            with orb.utils.io.open_hdf5(self.cube_path, 'r') as f:
                if not self._silent_load:
                    progress = ProgressBar(self.quad_nb)
                for iquad in range(self.quad_nb):
                    if not self._silent_load:
                        progress.update(iquad, info='Loading data')
                    x_min, x_max, y_min, y_max = self._get_quadrant_dims(
                        iquad, self.dimx, self.dimy, int(np.sqrt(float(self.quad_nb))))
                    if slice_in_quad(x_slice, x_min, x_max) and slice_in_quad(y_slice, y_min, y_max):
                        data[max(x_min, x_slice.start) - x_slice.start:
                             min(x_max, x_slice.stop) - x_slice.start,
                             max(y_min, y_slice.start) - y_slice.start:
                             min(y_max, y_slice.stop) - y_slice.start,
                             0:z_slice.stop-z_slice.start] = f[self._get_hdf5_quad_data_path(iquad)][
                            max(x_min, x_slice.start) - x_min:min(x_max, x_slice.stop) - x_min,
                            max(y_min, y_slice.start) - y_min:min(y_max, y_slice.stop) - y_min,
                            z_slice.start:z_slice.stop]
                if not self._silent_load:
                    progress.end()
                        

        return np.squeeze(data)

    def _get_attribute(self, attr, optional=False):
        """Return the value of an attribute of the HDF5 cube

        :param attr: Attribute to return
        
        :param optional: If True and if the attribute does not exist
          only a warning is raised. If False the HDF5 cube is
          considered as invalid and an exception is raised.
        """
        with orb.utils.io.open_hdf5(self.cube_path, 'r') as f:
            if attr in f.attrs:
                return f.attrs[attr]
            else:
                if not optional:
                    raise Exception('Attribute {} is missing. The HDF5 cube seems badly formatted. Try to create it again with the last version of ORB.'.format(attr))
                else:
                    return None
                   

