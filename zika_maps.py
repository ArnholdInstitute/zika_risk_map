#!/usr/bin/env python 
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

A few parameters we can change:
    - buffer_size: the size of the buffer around the A.A. mosquito location
      points. This increases the distribution of the mosquitoes, which means
      more population at risk.
    - population upper bound for mapping. The population distribution across
      census blocks follows a wicked power law. If we don't cap the
      population, then the legend will only focus on the very high population
      blocks. the map won't be legibile. I've set this to 1000 for now
    - proportion of counties with care delivery: as a mock up, I've set this
      to 0.7

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
import os

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
    
    return df_pop

def create_map( df, variable ):
    """
    Inputs:
        df - geodataframe
        variable - variable we want to map. Either 'risk_zone' or 'cold_spot'
    
    creating a colourbar for map
    it's clunky, geopandas doesn't do this well
    taken from a stackoverflow question
    """
    pop_min, pop_max = 1, 1000      # to keep colour scales interpretable
    
    ax = df[df[variable]==1].plot(
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
    if not(os.path.exists('./output')):
        os.mkdir('./output')
    fig.savefig('output/zika_map.png', dpi=300) 
    return 0 

def add_county_level_data( df_block ):
    """
    Adding in a layer of county level data.

    This mimics a situation where some counties have health care and others
    not.

    We represent this by a binary indicator

    Input: 
        df_block: geodataframe with sub county level geometry
    Returns:
        df: geodataframe with county and subcounty level geometry

    """
    # downloading county level shapefiles 
    county_fl = us.states.FL.shapefile_urls()['county']
    spatialfile = 'data/spatialfile.zip'
    urllib.urlretrieve(county_fl, spatialfile)
    zfile = zipfile.ZipFile(spatialfile)
    zfile.extractall('data/')

    # converting to a geodataframe
    df_county = gp.GeoDataFrame.from_file('data/tl_2010_12_county10.shp')

    # creating a dummy indicator = 1 if county 'has care delivery'
    prop_counties_w_care = 0.7      # proportion of counties with care
                                    # delivery
    care_delivery = random.rand(df.shape[0], 1)
    care_delivery = [ 1 if x < prop_counties_w_care else 0 for x in \
            care_delivery]
    df_county['care_delivery'] = care_delivery
    df_county.rename(columns 
            = { 'geometry' : 'geometry_county'},
            inplace=True)
    df = pd.merge(df_block, df_county, on='COUNTYFP10',
            how = 'left', indicator = True)

    # redefining risk zones to include a lack of care deliver
    # defined as cold spots
    cold_spots = (1 - df.care_delivery) * df.risk_zone
    df['cold_spots'] = cold_spots

    return df


    
if __name__=="__main__":
    print 'Creating database ...'
    df = aegypti_dist(0.15)
    df = add_county_level_data(df)
    print '... database created' 

    print 'Creating maps ...'
    create_map(df, 'risk_zones')
    create_map(df, 'cold_spots')
    print '... Map created!'
   
    print 'Saving shapefile'
    #Make sure `output` directory exists.  Make one if not
    if not(os.path.exists('./output')):
        os.mkdir('./output')
    df.to_file('output/zika_risk.shp')
    print 'Shapefile saved'


