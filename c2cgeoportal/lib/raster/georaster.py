# -*- coding: utf-8 -*-

# Copyright (c) 2012-2016, Camptocamp SA
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.


import os
from osgeo import gdal, ogr, osr


class Tile(object):
    def __init__(self, filename):
        self.filename = filename
        self.ds = None

    def get_value(self, x, y):
        if self.ds is None:
            self.ds = gdal.Open(self.filename)
            if self.ds is None:
                raise Exception("Could not open %s" % (self.filename))
            self.gt = self.ds.GetGeoTransform()
            self.rb = self.ds.GetRasterBand(1)
        px = int((x - self.gt[0]) / self.gt[1])
        py = int((y - self.gt[3]) / self.gt[5])
        val = self.rb.ReadAsArray(px, py, 1, 1)
        return val[0][0]


class GeoRaster:
    def __init__(self, shapefile_name):
        self.filename = shapefile_name
        self.folder = os.path.dirname(self.filename)
        if self.folder == "":
            self.folder = "."

        driver = ogr.GetDriverByName("ESRI Shapefile")
        self.ds = driver.Open(shapefile_name, 0)
        if self.ds is None:
            raise Exception("Could not open %s" % (shapefile_name))
        self.layer = self.ds.GetLayer()
        self.layerDef = self.layer.GetLayerDefn()
        self.srs = self.layer.GetSpatialRef()

        self.tiles = {}

    def get_value(self, x, y, srid):
        px, py = self.transform(x, y, srid)
        self.layer.SetSpatialFilterRect(px, py, px, py)
        tile = self._get_tile(px, py)
        if tile is None:
            return None
        return tile.get_value(px, py)

    def transform(self, x, y, srid):
        # if shp index srs is not known, suppose it is the same as viewer
        if self.srs is None:
            return (x, y)
        pt_srs = osr.SpatialReference()
        pt_srs.ImportFromEPSG(int(srid))
        transform = osr.CoordinateTransformation(pt_srs, self.srs)
        point = ogr.CreateGeometryFromWkt("POINT ({} {})".format(x, y))
        point.Transform(transform)
        return (point.GetX(), point.GetY())

    def _get_tile(self, x, y):
        self.layer.SetSpatialFilterRect(x, y, x, y)
        for feature in self.layer:
            location = feature.GetField("location")
            filename = location
            if not filename.startswith("/"):
                filename = os.path.join(self.folder, filename)
            if location not in self.tiles:
                self.tiles[location] = Tile(filename)
            tile = self.tiles[location]
            return tile
        return None
