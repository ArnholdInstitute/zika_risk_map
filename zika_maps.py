"""

Creating Zika risk maps

The risk map is based upon
    - population
    - distribution of A.Aegypti

For population we're using the 2010 census block level data. This data has the
highest spatial resolution we can get. We're explictly trading off temporal
resolution (for instance, we can get 2015 estimates at the census tract
level).

The distribution of A.Aegypti comes from https://elifesciences.org/content/4/e08347

"""
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
import pandas as pd
import geopandas as gp
import numpy as np
from shapely.geometry import Point
from shapely.ops import cascaded_union
import us
import zipfile
import urllib

def aegypti_dist(buffer_size):
    """
    Creates geo dataframe for A. Aegypti
    """

    ### loading a aegypti range data
    gd = gp.GeoDataFrame.from_csv('data/kraemer_etal_2015/global_aegypti.csv')
    # Keep only USA based estimates
    gd = gd[gd.COUNTRY_ID=='USA']
    # Turning coordinates into Shapely Points 
    points = [Point(x, y) for (x, y) in zip(gd.X, gd.Y)]
    points_a_aegypti = gp.GeoSeries(points)
    
    # restrict this to Florida
    # downloading Florida boundary shapefile
    fl_boundary_url = us.states.FL.shapefile_urls()['state']
    spatialfile = 'spatialfile.zip'
    urllib.urlretrieve(fl_boundary_url, spatialfile)
    zfile = zipfile.ZipFile(spatialfile)
    zfile.extractall('data/shapefiles/')
    gd_fl = gp.GeoDataFrame.from_file(
            'data/shapefiles/tl_2010_12_state10.shp')
    
    # keeping only AAegypti points that are in Florida
    fl_range = []
    for point in points_a_aegypti:
        if point.within(gd_fl.geometry[0]):
            fl_range.append(point)
    fl_range = gp.GeoSeries(fl_range)
    
    # cleaning up
    del gd_fl
    del points
    del points_a_aegypti

    # creating a buffer around these points
    # this is our spatial distribution of A. Aegypti
    fl_range_buffer = []
    for point in fl_range:
        fl_range_buffer.append(point.buffer(buffer_size))
    fl_range_buffer = gp.GeoSeries(fl_range_buffer)
    # merge the polygons together
    fl_range = cascaded_union(fl_range_buffer)
    
    ### loading population data
    df_pop = gp.GeoDataFrame.from_file(
        'data/tabblock2010_12_pophu/tabblock2010_12_pophu.shp')
    # removing areas with zero population
    df_pop = df_pop[df_pop.POP10!=0]
    
    # creating an indicator variable equal to one if the area of the census
    # block intersects with an aegypti buffer
    aa_range = []
    for polygon in df_pop.geometry:
        risk_zone = 0
        if polygon.intersects(fl_range):
            risk_zone = 1
        aa_range.append(risk_zone)
    
    df_pop['risk_zone'] = aa_range
    
    df_pop.to_file('data/zika_risk.shp')
    print 'Shapefile saved'
    # creating a colourbar for map
    # it's clunky, geopandas doesn't do this well
    # taken from a stackoverflow question
    print 'Making graph' 
    pop_min, pop_max = 1, 1000      # to keep colour scales interpretable
    
    ax = df_pop[df_pop.risk_zone==1].plot(
        column='POP10', cmap = 'OrRd',
        vmin = pop_min, vmax = pop_max,
        linewidth = 0)
    # add colorbar
    fig = ax.get_figure()
    cax = fig.add_axes([0.9, 0.1, 0.3, 0.8])
    sm = plt.cm.ScalarMappable(cmap='OrRd', 
        norm = plt.Normalize(vmin = pop_min, vmax = pop_max))
    # clunky but needed
    sm._A = []
    fig.colorbar(sm, cax=cax)
    fig.savefig('zika_test.png', dpi=300) 
    
    return 0

    
if __name__=="__main__":
    print 'Creating risk map ...'
    aegypti_dist(0.15)
    print '... Map created!'



