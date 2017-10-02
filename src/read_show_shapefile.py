# read and show shapefile
from sys import argv
import shapefile
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from descartes.patch import PolygonPatch

import geopandas as gpd

"""
 IMPORT SHAPEFILE
"""
shapefile_base_path = argv[1]
#csv_file = argv[2]
map_path = argv[2]

# shp_file_base='2010_census_tracts_nyc'
# dat_dir='../data/shapefiles/census_tract/2010/'
# shape_file = shapefile.Reader(dat_dir+shp_file_base)

'''
		ACCESS CONTENT
'''
def get_shape_content(shape_file):

	list_shape_content = []

	fields = shape_file.fields[1:]
	field_names = [field[0] for field in fields]

	for row in shape_file.iterShapeRecords():
		list_shape_content.append(dict(zip(field_names, row.record)))

	return list_shape_content

def get_records_shapes(shape_file):

	fields = shape_file.fields[1:]
	field_names = [field[0] for field in fields]

	list_records = []
	for record, shape in zip(shape_file.iterRecords(), shape_file.iterShapes()):
		# All of the shapes in the TM_WORLD_BORDERS dataset have shape.shapeType == 5
		list_records.append(dict(zip(field_names, record)))

	return pd.DataFrame(list_records)

def save_records_to_csv(shape_file, csv_file):
    df_shape_records = get_records_shapes(shape_file)
    df_shape_records = get_records_shapes(shape_file)
    #del df_shape_records['url']
    print df_shape_records

    df_shape_records.to_csv(csv_file)

'''
    PLOTTING
'''

''' PLOTS A SINGLE SHAPE '''
def plot_single_shape(shape_file, map_file):
	fig, ax = plt.subplots()

	plt.figure()
	#ax = plt.axes()
	ax.set_aspect('equal')
	shape_ex = shape_file.shape(5)
	x_lon = np.zeros((len(shape_ex.points),1))
	y_lat = np.zeros((len(shape_ex.points),1))
	for ip in range(len(shape_ex.points)):
	    x_lon[ip] = shape_ex.points[ip][0]
	    y_lat[ip] = shape_ex.points[ip][1]

	ax.plot(x_lon,y_lat,'k')

	# use bbox (bounding box) to set plot limits
	ax.set_xlim(shape_ex.bbox[0],shape_ex.bbox[2])

	fig.savefig('map_file')

''' PLOTS ALL SHAPES '''
def plot_all_shapes(shape_file, map_path):
	title = 'Borough'

	#facecolor = '#6699cc'
	facecolor = '#99ccff'
	#facecolor = '#cccccc'

	fig = plt.figure()
	ax = fig.gca()

	#icolor = 1
	for shape in list(shape_file.iterShapes()):

	    # define polygon fill color (facecolor) RGB values:
	    # R = (float(icolor)-1.0)/52.0
	    # G = 0
	    # B = 0acecolor, linewidth=.25)
	        ax.add_patch(patch)

	    else: # loop over parts of each shape, plot separately
	        for ip in range(nparts): # loop over parts, plot separately
	            i0=shape.parts[ip]
	            if ip < nparts-1:
	               i1 = shape.parts[ip+1]-1
	            else:
	               i1 = len(shape.points)

	            polygon = Polygon(shape.points[i0:i1+1])
	            patch = PolygonPatch(polygon, alpha=1.0, zorder=2, facecolor=facecolor, linewidth=.25)
	            ax.add_patch(patch)

	    #icolor = icolor + 1
	ax.axis('scaled')
	ax.set_title(title)
	fig.tight_layout()
	fig.savefig(map_path)

'''
    Plot map, censustract, station
'''
nyc_map = gpd.read_file(shapefile_base_path)
print nyc_map

fig, ax = plt.subplots()
ax.set_aspect('equal')
nyc_map.plot(ax=ax, color='white')

fig.savefig(map_path)

#shape_file = shapefile.Reader(shapefile_base_path)
#save_records_to_csv(shape_file, csv_file)
#plot_all_shapes(shape_file, map_path)
