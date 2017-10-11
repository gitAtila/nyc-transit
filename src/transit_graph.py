#read edges and build a graph of the transit system
from sys import argv, maxint
from geopy.distance import vincenty
import pandas as pd
import geopandas as gpd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import linemerge, unary_union

stations_path = argv[1]
lines_path = argv[2]
links_path = argv[3]
census_tract_path = argv[4]
result_folder = argv[5]
tolerance = 11 # meters

def get_subgraph_node(graph, node_key, node_value):
    list_node = []
    for key, dict_attribute in graph.nodes_iter(data=True):
        if dict_attribute[node_key] == node_value:
            list_node.append(key)
    subgraph = graph.subgraph(list_node)
    return subgraph

def get_subgraph_edge(graph, edge_key, edge_value):
    list_node = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        if dict_attribute[edge_key] == edge_value:
            if u not in list_node:
                list_node.append(u)
            if v not in list_node:
                list_node.append(v)
    return graph.subgraph(list_node)

def unique_node_values(graph, node_key):
    return list(set([graph.node[index][node_key] for index in graph]))

def unique_edge_values(graph, edge_key):
    list_attribute = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        list_attribute.append(dict_attribute[edge_key])
    return list(set(list_attribute))

def distance_points(point_lon_lat_A, point_lon_lat_B):
    return vincenty((point_lon_lat_A[1], point_lon_lat_A[0]),\
     (point_lon_lat_B[1], point_lon_lat_B[0])).meters

'''
    Read stations, subay lines and links between stations
'''

gdf_stations = gpd.GeoDataFrame.from_file(stations_path)
gdf_lines = gpd.GeoDataFrame.from_file(lines_path)
df_links = pd.read_csv(links_path)

'''
    Get subway lines and trunks
'''

# get subway trunks
dict_line_trunk = dict()
dict_trunk_lines = dict()
for index, line in gdf_lines.iterrows():
    dict_line_trunk[line['name']] = line['rt_symbol']
    dict_trunk_lines.setdefault(line['rt_symbol'],[]).append(line['name'])

'''
    Create subway graph
'''

def create_transit_graph(graph_constructor, gdf_stations, df_links):
    g_transit = graph_constructor
    # add stations to subway graph
    for index, station in gdf_stations.iterrows():
        g_transit.add_node(station['objectid'], name=station['name'], line=station['line'],\
         notes=station['notes'], posxy=(station['geometry'].x, station['geometry'].y))

    # add links to subway graph
    for index, link in df_links.iterrows():
        if link['node_1'] in g_transit.nodes() and link['node_2'] in g_transit.nodes():
            # compute link distance
            distance = distance_points(g_transit.node[link['node_1']]['posxy'], g_transit.node[link['node_2']]['posxy'])
            g_transit.add_edge(link['node_1'], link['node_2'], trunk=link['trunk'], distance=distance)
        else:
        	print link['node_1'] + 'and' + link['node_2'] + 'are not present in graph'

    return g_transit

def touches(linestring_1, linestring_2, tolerance):
    if touches_extremities(linestring_1, linestring_2, tolerance)\
     or touches_extremity_line(linestring_1, linestring_2, tolerance):
        return True
    return False

def touches_extremities(linestring_1, linestring_2, tolerance):
    #tolerance = 2 #meters
    left_1 = Point(linestring_1.coords[0])
    right_1 = Point(linestring_1.coords[-1])

    left_2 = Point(linestring_2.coords[0])
    right_2 = Point(linestring_2.coords[-1])

    distance_ll = vincenty((left_1.x, left_1.y), (left_2.x, left_2.y)).meters
    distance_lr = vincenty((left_1.x, left_1.y), (right_2.x, right_2.y)).meters
    distance_rl = vincenty((right_1.x, right_1.y), (left_2.x, left_2.y)).meters
    distance_rr = vincenty((right_1.x, right_1.y), (right_2.x, right_2.y)).meters

    if distance_lr <= tolerance or distance_lr <= tolerance or distance_ll <= tolerance\
     or distance_rr <= tolerance:
        return True

    return False

def distance_point_line(point, linestring):
    projection = linestring.interpolate(linestring.project(point))
    distance = vincenty((point.x, point.y), (projection.x, projection.y)).meters
    return distance

# verify if an extremity of a line touches the other line
def touches_extremity_line(linestring_1, linestring_2, tolerance):
    left_1 = Point(linestring_1.coords[0])
    right_1 = Point(linestring_1.coords[-1])

    left_2 = Point(linestring_2.coords[0])
    right_2 = Point(linestring_2.coords[-1])

    distance_left1_line2 = distance_point_line(left_1, linestring_2)
    distance_right1_line2 = distance_point_line(right_1, linestring_2)
    distance_left2_line1 = distance_point_line(left_2, linestring_1)
    distance_right2_line1 = distance_point_line(right_2, linestring_1)

    if distance_left1_line2 <= tolerance or distance_right1_line2 <= tolerance\
     or distance_left2_line1 <= tolerance or distance_right2_line1 <= tolerance:
        return True
    return False

# create a graph connecting each linestring of the same trunk that touches each other
def create_line_graph(gdf_lines):
    g_lines = nx.Graph()
    list_unique_trunks = gdf_lines['rt_symbol'].unique()
    for trunk in list_unique_trunks:
        gdf_trunk_line = gdf_lines[gdf_lines['rt_symbol'] == trunk]
        for index_1 ,line_1 in gdf_trunk_line.iterrows():
            for index_2 ,line_2 in gdf_trunk_line.iterrows():
                # There are not loops
                if index_1 != index_2 and touches(line_1['geometry'], line_2['geometry'], tolerance):
                    g_lines.add_edge(index_1, index_2, trunk=trunk,\
                     weight = line_1['shape_len'] + line_2['shape_len'])
    return g_lines

def linemerge_sequential(multilinestring):
    # initialize list_linestring with the first one
    first_linestring = multilinestring[0]
    list_linestrings = list(first_linestring.coords)

    # get extremity values
    right_pos_line = first_linestring.coords[-1]
    left_pos_line = first_linestring.coords[0]

    #print last_position
    for index in range(1,len(multilinestring)):
        linestring = list(multilinestring[index].coords)
        dict_dist = dict()

        # compute the distance between linestring extremities
        dict_dist['dist_rr'] = vincenty(right_pos_line, linestring[-1])
        dict_dist['dist_rl'] = vincenty(right_pos_line, linestring[0])
        dict_dist['dist_lr'] = vincenty(left_pos_line, linestring[-1])
        dict_dist['dist_ll'] = vincenty(left_pos_line, linestring[0])

        # get the shortest distance
        min_dist = min(dict_dist, key=dict_dist.get)

        if min_dist=='dist_rr':
            print min_dist
            list_linestrings = list_linestrings + linestring[::-1]
        elif min_dist=='dist_rl':
            print min_dist
            list_linestrings = list_linestrings + linestring
        elif min_dist=='dist_lr':
            # reverse both lists
            print min_dist
            list_linestrings = list_linestrings[::-1] + linestring[::-1]
        else: # min_dist =='dist_ll'
            print min_dist
            list_linestrings = list_linestrings[::-1] + linestring

        # update extremities
        right_pos_line = list_linestrings[-1]
        left_pos_line = list_linestrings[0]

    return LineString(list_linestrings)

def linestring_through_points(gdf_trunk_line, g_trunk_line, id_linestring_s1, id_linestring_s2):

    linestring_s1 = gdf_trunk_line.loc[id_linestring_s1]['geometry']
    linestring_s2 = gdf_trunk_line.loc[id_linestring_s2]['geometry']

    # if points lie on the same linestring
    if id_linestring_s1 == id_linestring_s2:
        return  linestring_s1

    # linestring_s1 and linestring_s2 touches each other
    if touches(linestring_s1, linestring_s2, tolerance):
        merged_linestrings = [linestring_s1, linestring_s2]
        merged_linestrings = MultiLineString(merged_linestrings)
        merged_linestrings = linemerge(merged_linestrings)
        if type(merged_linestrings) == MultiLineString:
            merged_linestrings = linemerge_sequential(merged_linestrings)
        return merged_linestrings

    # if there are one or more linestrings between linestring_s1 and linestring_s2
    else:
        # path of linestrings
        try:
            linestrings_path = nx.dijkstra_path(g_trunk_line, id_linestring_s1, id_linestring_s2, weight='weight')

        # there is no path between stations
        except:
            for u, v , dict_trunk in g_trunk_line.edges_iter(data=True):
                print gdf_trunk_line.loc[u]['id'], '-->', gdf_trunk_line.loc[v]['id']
            last_point = gdf_trunk_line.loc[id_linestring_s1]['geometry'].coords[-1]
            first_point = gdf_trunk_line.loc[id_linestring_s2]['geometry'].coords[0]
            #first_point = gdf_trunk_line[gdf_trunk_line['id'] == 2000058.0]['geometry'].iloc[0].coords[0]
            print vincenty(last_point, first_point).meters
            print 'There is no path between', id_linestring_s1, 'and', id_linestring_s2
            return None

        # get linestrings by its indexes
        list_betweeness = []
        for index in linestrings_path:
            list_betweeness.append(gdf_trunk_line.loc[index])
            print gdf_trunk_line.loc[index]['id']
        gdf_betweeness = gpd.GeoDataFrame(list_betweeness, geometry='geometry')

        # merge linestrings
        merged_linestrings = gdf_betweeness['geometry'].tolist()
        merged_linestrings = MultiLineString(merged_linestrings)
        merged_linestrings = linemerge(merged_linestrings)
        if type(merged_linestrings) == MultiLineString:
            merged_linestrings = linemerge_sequential(merged_linestrings)
        return merged_linestrings

    return None

# get the nearest point on a linestring
def nearest_point_linestring(linestring, point):
    nearest_point = -1
    shortest_distance = maxint
    for index in range(len(linestring.coords)):
        distance = vincenty((point.x, point.y), linestring.coords[index]).meters
        if distance < shortest_distance:
            shortest_distance = distance
            nearest_point = index
    return nearest_point

def nearest_linestring_point(gdf_trunk_line, point):
    min_distance = maxint
    nearest_linestring_id = -1
    for index, linestring in gdf_trunk_line.iterrows():
        distance = float(point.distance(linestring['geometry']))
        if distance < min_distance:
            min_distance = distance
            nearest_linestring_id = index
    return nearest_linestring_id

def cut_line_at_points(line, points):
    # First coords of line
    coords = list(line.coords)

    # Keep list coords where to cut (cuts = 1)
    cuts = [0] * len(coords)
    cuts[0] = 1
    cuts[-1] = 1

    # Add the coords from the points
    coords += [list(p.coords)[0] for p in points]
    cuts += [1] * len(points)

    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]

    # sort the coords/cuts based on the distances
    coords = [p for (d, p) in sorted(zip(dists, coords))]
    cuts = [p for (d, p) in sorted(zip(dists, cuts))]

    # generate the Lines
    lines = []
    for i in range(len(coords)-1):
        if cuts[i] == 1:
            # find next element in cuts == 1 starting from index i + 1
            j = cuts.index(1, i + 1)
            lines.append(LineString(coords[i:j+1]))

    return lines

def linestring_between_points(linestring, point_1, point_2):
    # get cut points
    proj_point1 = linestring.interpolate(linestring.project(point_1))
    proj_point2 = linestring.interpolate(linestring.project(point_2))

    # cut linestring given projection point
    inline = cut_line_at_points(linestring, [proj_point1, proj_point2])[1]

    return inline

def split_linestring(point, linestring):
    nearest_point = -1
    shortest_distance = maxint
    for index in range(len(linestring.coords)):
        distance = vincenty(point, linestring.coords[index]).meters
        if distance < shortest_distance:
            shortest_distance = distance
            nearest_point = index

    linestring = list(linestring_s1.coords)

    linestring_part_1 = linestring[:nearest_point]
    linestring_part_2 = linestring[nearest_point:]
    print 'len left', len(linestring_part_1)
    print 'len right', len(linestring_part_2)

    if len(linestring_part_1) > 1:
        linestring_part_1 = LineString(linestring_part_1)
    elif len(linestring_part_1) == 1:
        linestring_part_1 = Point(linestring_part_1)
    else:
        linestring_part_1 = []

    if len(linestring_part_2) > 1:
        linestring_part_2 = LineString(linestring_part_2)
    elif len(linestring_part_2) == 1:
        linestring_part_2 = Point(linestring_part_2)
    else:
        linestring_part_2 = []

    return linestring_part_1, linestring_part_2

def path_between_stops(df_links, gdf_stations, gdf_lines, g_lines):
    list_geolinks = []
    # get the path between stations
    for index, link in df_links.iterrows():

        stop_1 = gdf_stations[gdf_stations['objectid'] == link['node_1']]
        stop_2 = gdf_stations[gdf_stations['objectid'] == link['node_2']]

        gdf_trunk_line = gdf_lines[gdf_lines['rt_symbol'] == link['trunk']]
        g_trunk_line = get_subgraph_edge(g_lines, 'trunk', link['trunk'])

        # find the nearest linestrings on point
        nearest_linestring_s1 = nearest_linestring_point(gdf_trunk_line, stop_1)
        nearest_linestring_s2 = nearest_linestring_point(gdf_trunk_line, stop_2)

        print 'trunk', link['trunk']

        print 'stop_1', stop_1['objectid'].iloc[0]
        print 'stop_2', stop_2['objectid'].iloc[0]

        print 'nearest_linestring_s1', gdf_trunk_line.loc[nearest_linestring_s1]['id']
        print 'nearest_linestring_s2', gdf_trunk_line.loc[nearest_linestring_s2]['id']

        # get linestrings near stations point
        gdf_trunk_line_s1 = gdf_trunk_line.loc[nearest_linestring_s1]
        gdf_trunk_line_s2 = gdf_trunk_line.loc[nearest_linestring_s2]

        linestring_s1 = gdf_trunk_line_s1['geometry']
        linestring_s2 = gdf_trunk_line_s2['geometry']

        # print linestring_s1
        # print linestring_s2

        linestring_s1 = LineString(linestring_s1)
        linestring_s2 = LineString(linestring_s2)

        # get coordinates of station
        point_s1 = stop_1['geometry']
        point_s2 = stop_2['geometry']

        point_s1 = Point(stop_1['geometry'].iloc[0])
        point_s2 = Point(stop_2['geometry'].iloc[0])

        # get merged set of linestrings that pass through poits s1 and s2
        merged_linestrings = linestring_through_points(gdf_trunk_line, g_trunk_line,\
         nearest_linestring_s1, nearest_linestring_s2)

        #print merged_linestrings

        #break
        if merged_linestrings is None:
            print 'untreated case'

            # plot edges and points
            fig, ax = plt.subplots()
            ax.set_aspect('equal')
            ax.axis('off')
            x, y = linestring_s1.xy
            ax.plot(x,y, color='blue')
            x, y = linestring_s2.xy
            ax.plot(x,y, color='red')
            x, y = point_s1.xy
            ax.scatter(x,y, color='black')
            x, y = point_s2.xy
            ax.scatter(x,y, color='black')
            fig.savefig(result_folder + 'error_path_between_stops.pdf')

            # print stop_1['objectid']
            # if stop_1['objectid'].iloc[0] == 469.0:
            #     print 'jump'
            # else:
            #     break

        else:
            # split linestrings given stops
            edge = linestring_between_points(merged_linestrings, point_s1, point_s2)
            geo_link = link.to_dict()
            geo_link['geometry'] = edge
            list_geolinks.append(geo_link)

            if stop_1['objectid'].iloc[0] == 435  and stop_2['objectid'].iloc[0] == 15:

                # plot edges and points
                fig, ax = plt.subplots()
                ax.set_aspect('equal')
                ax.axis('off')

                x, y = merged_linestrings.xy
                ax.plot(x,y, color='purple')

                x, y = linestring_s1.xy
                ax.plot(x,y, color='blue')
                x, y = linestring_s2.xy
                ax.plot(x,y, color='red')

                x, y = edge.xy
                ax.plot(x,y, color='green')

                x, y = point_s1.xy
                ax.scatter(x,y, color='black')
                x, y = point_s2.xy
                ax.scatter(x,y, color='black')
                fig.savefig(result_folder + 'path_between_stops.pdf')
                #break

    print len(list_geolinks[0])
    gdf_geolinks = gpd.GeoDataFrame(list_geolinks, geometry='geometry')
    return gdf_geolinks

'''
    Get the best subway path from one station to a census tract
'''

def stations_near_point_per_trunk(g_transit, gs_point):
    list_trunk_stations = list()
    list_unique_trunks = unique_edge_values(g_transit, 'trunk')
    print list_unique_trunks
    # Find out the nearest station from point for each line trunk
    dict_stations_trunk = dict()
    for trunk in list_unique_trunks:
        g_trunk = get_subgraph_edge(g_transit, 'trunk', trunk)
        # get the nearest station
        shortest_distance = maxint
        best_station = -1
        for node_key, dict_attribute in g_trunk.nodes_iter(data=True):
            distance =  distance_points(dict_attribute['posxy'], (gs_point.iloc[0].x, gs_point.iloc[0].y))
            if distance < shortest_distance:
                shortest_distance = distance
                best_station = node_key
        dict_stations_trunk[trunk] = {'station':best_station ,'distance': shortest_distance}

    # stations of transference were already inserted
    del dict_stations_trunk['T']

    return dict_stations_trunk

def best_route_shortest_walk_distance(dict_trip_trunks):
    shortest_distance = maxint
    nearest_trunk = -1
    for trunk, destination_station in dict_trip_trunks.iteritems():
        if destination_station['distance'] < shortest_distance:
            shortest_distance = destination_station['distance']
            nearest_trunk = trunk

    best_destination = dict_trip_trunks[nearest_trunk]
    best_destination['trunk'] = nearest_trunk

    return best_destination

'''
    Plot graph
'''

def plot_gdf(gdf, plot_name):
    fig, ax = plt.subplots()
    ax.set_aspect('equal')
    ax.axis('off')
    gdf.plot(ax=ax)

    fig.savefig(plot_name)

def plot_graph(graph, unique_keys, color_field,  file_name):
    print unique_keys
    # set colors to stations acording with its line
    color_map = dict()
    cmap = plt.get_cmap('prism')
    colors = cmap(np.linspace(0,1,len(unique_keys)))
    for key in range(len(unique_keys)):
        color_map[unique_keys[key]] = colors[key]
    #plot color
    positions = nx.get_node_attributes(graph, 'posxy')
    node_color=[color_map[graph.node[node][color_field]] for node in graph]
    nx.draw(graph, positions, node_color=node_color, cmap=plt.get_cmap('jet'), node_size=5,\
     font_size=5, with_labels=False)
    plt.savefig(file_name, dpi=1000)

def plot_transit_graph(transit_graph, result_file_name):
    # # set nodes color according to lines
    # ## get unique lines
    # unique_lines = list(gdf_stations['line'].unique())
    # ## define color range
    # cmap = plt.get_cmap('prism')
    # ## set color to nodes
    # colors = cmap(np.linspace(0,1,len(unique_lines)))
    # color_map = dict()
    # for line in range(len(unique_lines)):
    #     color_map[unique_lines[line]] = colors[line]
    # node_color = [color_map[transit_graph.node[node]['line']] for node in transit_graph]
    node_color = '#000000'

    # set edges color according to trunks
    ## get official colors
    trunk_colors = {'1':'#ee352e', '4':'#00933c', '7':'#b933ad', 'A':'#2850ad', 'B':'#ff6319',\
     'G':'#6cbe45', 'J':'#996633', 'L':'#a7a9ac', 'N':'#fccc0a', 'T':'#000000'}
    ## set colors to edges
    edge_color = [trunk_colors[transit_graph[u][v]['trunk']] for u,v in transit_graph.edges()]
    #edge_color = '#ff6319'

    # set node positions according to geographical positions of stations
    node_position = nx.get_node_attributes(transit_graph, 'posxy')

    # plot and save graph
    nx.draw(transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=0.5, linewidths=0.5 , with_labels=False)
    plt.savefig(result_file_name, dpi=1000)

def plot_path(transit_graph, list_stations, result_file_name):
    # plot complete transit graph
    node_position = nx.get_node_attributes(transit_graph, 'posxy')
    node_color = '#000000'
    edge_color = '#a7a9ac'
    nx.draw(transit_graph, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=0.2, linewidths=0.5 , with_labels=False)

    # plot trip path
    trip_path = transit_graph.subgraph(list_stations)
    node_position = nx.get_node_attributes(trip_path, 'posxy')
    node_color = '#a7a9ac'
    edge_color = '#000000'
    nx.draw(trip_path, node_position, node_color=node_color, edge_color=edge_color,\
     node_size=1, alpha=1, linewidths=0.5 , with_labels=False)

    plt.savefig(result_file_name, dpi=1000)

'''
    Test area
'''

# get links between stations for all subway trunks
list_geolinks = []
list_unique_trunks = gdf_lines['rt_symbol'].unique()
#list_unique_trunks = ['N']
for trunk in list_unique_trunks:
    gdf_lines_trunk = gdf_lines[gdf_lines['rt_symbol'] == trunk]
    print 'Trunk:', trunk
    if trunk == 'B':
        # delete unnecessary edge
        gdf_lines_trunk = gdf_lines_trunk[gdf_lines_trunk['id'] != 2000293]

        # create a graph with subway lines
        g_lines = create_line_graph(gdf_lines_trunk)

        # add necessary edge where lines are too far each other
        index_1 = gdf_lines_trunk[gdf_lines_trunk['id'] == 2000292].index.values.tolist()[0]
        index_2 = gdf_lines_trunk[gdf_lines_trunk['id'] == 2000294].index.values.tolist()[0]
        g_lines.add_edge(index_1, index_2, trunk=trunk)

    else:
        # create a graph with subway lines
        g_lines = create_line_graph(gdf_lines_trunk)

    # get subway links between stations
    df_links_trunk = df_links[df_links['trunk'] == trunk]
    print 'df_links', len(df_links_trunk)
    print 'gdf_stations', len(gdf_stations)
    print 'gdf_lines', len(gdf_lines)
    print 'g_lines', len(g_lines)
    gdf_geolinks_trunk = path_between_stops(df_links_trunk, gdf_stations, gdf_lines_trunk, g_lines)

    print gdf_geolinks_trunk

    list_geolinks.append(gdf_geolinks_trunk)
    #plot_gdf(gdf_geolinks, result_folder + 'geolinks_' + trunk + '.pdf')
    # save links as shapefile
gdf_geolinks = gpd.GeoDataFrame(pd.concat(list_geolinks, ignore_index=True))
gdf_geolinks.to_file(result_folder+'links.shp')


'''
g_transit = create_transit_graph(nx.Graph(), gdf_stations, df_links)
#g_transit = create_transit_graph(nx.MultiGraph(), gdf_stations, df_links)
#split_line_route(gdf_stations, gdf_lines, df_links)

gdf_census_tract = gpd.GeoDataFrame.from_file(census_tract_path)
first_subway_boarding = 49
ct_origin = '012600'
ct_destination = '024100'
boro_destination = '2'

# discover which was the alight station
## get the centroid of the census tract
gs_destination = gdf_census_tract[gdf_census_tract['ct2010'] == ct_destination]
gs_destination = gs_destination[gs_destination['boro_code'] == boro_destination]
destination_centroid = gs_destination.centroid

## get the stations nearby centroid
dict_trunk_stations_near_destination = stations_near_point_per_trunk(g_transit, destination_centroid)

# construct probable trips
dict_best_trunk_station = best_route_shortest_walk_distance(dict_trunk_stations_near_destination)
trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, dict_best_trunk_station['station'],\
 weight='distance')

# dict_trip_trunks = dict()
# for trunk, destination_station in trunk_stations.iteritems():
#     print trunk, destination_station
#     trip_path = nx.dijkstra_path(g_transit, first_subway_boarding, destination_station['station'],\
#      weight='distance')
#     dict_trip_trunks[trunk] = trip_path
#     print trip_path
#     print ''
'''
