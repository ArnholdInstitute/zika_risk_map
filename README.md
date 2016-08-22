# Zika risk map

Constructing a map of Zika risk in Florida

Zika risk is defined as the population at risk of contracting Zika from
the _Aedes Aegypti_ mosquito. This means we are ignoring travel and sexually
transmitted infections.

The two main datasets we have:
- [_A. Aegypti_ range](https://elifesciences.org/content/4/e08347). 

- [Population](https://www.census.gov/geo/maps-data/data/tiger-data.html). The 2010 census block population. You'll have to download it yourself as it's larger that GitHub will allow.

From these I take a population map, and mask out any populations that do not
lie within the historical range of _A. Aegypti_.

There is one script [zika_maps.py](). Running the script will
save a shapefile of the risk, with a map.

To run this you'll need some spatial
libraries:

- [Shapely](http://toblerity.org/shapely/manual.html)
- [Geopandas](http://geopandas.org)

And all their dependencies. In addition, the [US](https://pypi.python.org/pypi/us) python library is used to get a map of Florida's boundaries. 





