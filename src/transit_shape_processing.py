'''
    Read lines and stops and get the paths between stops
'''

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
result_folder = argv[4]
tolerance = 11 # meters

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
    Graph operations
'''

def get_subgraph_edge(graph, edge_key, edge_value):
    list_node = []
    for u, v, dict_attribute in graph.edges_iter(data=True):
        if dict_attribute[edge_key] == edge_value:
            if u not in list_node:
                list_node.append(u)
            if v not in list_node:
                list_node.append(v)
    return graph.subgraph(list_node)

'''
    Read shapefile and get geometry path between stations
'''

# from:https://stackoverflow.com/questions/34754777/shapely-split-linestrings-at-intersections-with-other-linestrings
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

def split_intersection(linestring_1, linestring_2, touch_way):
    extremity = touch_way[0]
    touched_line = touch_way[1]

    if touched_line == '1':
        if extremity == 'r':
            point = Point(linestring_2.coords[-1])
        else:
            point = Point(linestring_2.coords[0])

        projection = linestring_1.interpolate(linestring_1.project(point))
        lines = cut_line_at_points(linestring_1, [projection, projection])

    else:
        if extremity == 'r':
            point = Point(linestring_1.coords[-1])
        else:
            point = Point(linestring_1.coords[0])

        projection = linestring_2.interpolate(linestring_2.project(point))
        lines = cut_line_at_points(linestring_2, [projection, projection])

    # print nothing
    return lines[0], lines[2]

def preprocess_lines(gdf_lines):
    deletion_list = []
    insertion_list = []
    # find the cases when a line touces the extremity of the other
    list_unique_trunks = gdf_lines['rt_symbol'].unique()
    for trunk in list_unique_trunks:
        gdf_trunk_line = gdf_lines[gdf_lines['rt_symbol'] == trunk]
        # print gdf_trunk_line
        # print nothing
        for index_1 ,line_1 in gdf_trunk_line.iterrows():
            for index_2 ,line_2 in gdf_trunk_line.iterrows():
                # There are not loops
                if index_1 != index_2:
                    touch_way = touches(line_1['geometry'], line_2['geometry'], tolerance)
                    if type(touch_way) == str:

                        # split linestring where the extremity touches
                        slice_1, slice_2 = split_intersection(line_1['geometry'], line_2['geometry'],touch_way)

                        # delete splitted linestring
                        if touch_way[1] == '1' and index_1 not in deletion_list:
                            print line_1['objectid'], '-->', line_2['objectid']

                            deletion_list.append(index_1)
                            # get attributes from original line
                            dict_slice_1 = gdf_trunk_line.loc[index_1].to_dict()
                            dict_slice_2 = gdf_trunk_line.loc[index_1].to_dict()

                            # update geometrical attributes
                            dict_slice_1['geometry'] = slice_1
                            dict_slice_1['shape_len'] = distance_linestring(slice_1)

                            dict_slice_2['geometry'] = slice_2
                            dict_slice_2['shape_len'] = distance_linestring(slice_2)

                            # append new slices
                            insertion_list.append(dict_slice_1)
                            insertion_list.append(dict_slice_2)

                        elif touch_way[1] == '2' and index_2 not in deletion_list:
                            print line_1['objectid'], '-->', line_2['objectid']

                            deletion_list.append(index_2)
                            # get attributes from original line
                            dict_slice_1 = gdf_trunk_line.loc[index_2].to_dict()
                            dict_slice_2 = gdf_trunk_line.loc[index_2].to_dict()

                            # update geometrical attributes
                            dict_slice_1['geometry'] = slice_1
                            dict_slice_1['shape_len'] = distance_linestring(slice_1)

                            dict_slice_2['geometry'] = slice_2
                            dict_slice_2['shape_len'] = distance_linestring(slice_2)

                            # append new slices
                            insertion_list.append(dict_slice_1)
                            insertion_list.append(dict_slice_2)

    if len(deletion_list) > 0:
        # delete splitted lines
        for del_index in deletion_list:
            print del_index
            gdf_lines.drop(del_index, inplace=True)

        # insert slices
        gdf_splitted = gpd.GeoDataFrame(insertion_list, geometry='geometry')
        gdf_lines = pd.concat([gdf_lines, gdf_splitted])
        gdf_lines = gdf_lines.reset_index()
        print gdf_lines

        return gpd.GeoDataFrame(gdf_lines, geometry='geometry')

    return gdf_lines


def touches(linestring_1, linestring_2, tolerance):
    if touches_extremities(linestring_1, linestring_2, tolerance):
        return 1
    else:
        touches_value = touches_extremity_line(linestring_1, linestring_2, tolerance)
        if touches_value != -1:
            return touches_value
    return -1

def touches_extremities(linestring_1, linestring_2, tolerance):
    #tolerance = 2 #meters
    left_1 = Point(linestring_1.coords[0])
    right_1 = Point(linestring_1.coords[-1])

    left_2 = Point(linestring_2.coords[0])
    right_2 = Point(linestring_2.coords[-1])

    dict_dist = dict()
    dict_dist['ll'] = vincenty((left_1.x, left_1.y), (left_2.x, left_2.y)).meters
    dict_dist['lr'] = vincenty((left_1.x, left_1.y), (right_2.x, right_2.y)).meters
    dict_dist['rl'] = vincenty((right_1.x, right_1.y), (left_2.x, left_2.y)).meters
    dict_dist['rr'] = vincenty((right_1.x, right_1.y), (right_2.x, right_2.y)).meters

    # get the shortest distance
    min_dist_key = min(dict_dist, key=dict_dist.get)

    if dict_dist[min_dist_key] <= tolerance:
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

    # compute the distance between linestring extremities
    dict_dist = dict()
    dict_dist['l2'] = distance_point_line(left_1, linestring_2)
    dict_dist['r2'] = distance_point_line(right_1, linestring_2)
    dict_dist['l1'] = distance_point_line(left_2, linestring_1)
    dict_dist['r1'] = distance_point_line(right_2, linestring_1)

    # get the shortest distance
    min_dist_key = min(dict_dist, key=dict_dist.get)

    if dict_dist[min_dist_key] <= tolerance:
        return min_dist_key
    else:
        return -1

# create a graph connecting each linestring of the same trunk that touches each other
def create_line_graph(gdf_lines):
    g_lines = nx.Graph()
    list_unique_trunks = gdf_lines['rt_symbol'].unique()
    for trunk in list_unique_trunks:
        gdf_trunk_line = gdf_lines[gdf_lines['rt_symbol'] == trunk]
        for index_1 ,line_1 in gdf_trunk_line.iterrows():
            for index_2 ,line_2 in gdf_trunk_line.iterrows():
                # There are not loops
                if index_1 != index_2\
                 and touches(line_1['geometry'], line_2['geometry'], tolerance) == 1:
                    g_lines.add_edge(index_1, index_2, trunk=trunk,\
                     weight = line_1['shape_len'] + line_2['shape_len'])
    return g_lines

def distance_linestring(linestring):
    total_distance = []
    previous_position = linestring.coords[0]
    for index in range(1, len(linestring.coords)):
        actual_position = linestring.coords[index]
        total_distance = vincenty(previous_position, actual_position).meters
        previous_position = actual_position
    return total_distance

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
    if touches(linestring_s1, linestring_s2, tolerance) == 1:
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
                print gdf_trunk_line.loc[u]['objectid'], '-->', gdf_trunk_line.loc[v]['objectid']
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
            print gdf_trunk_line.loc[index]['objectid']
        gdf_betweeness = gpd.GeoDataFrame(list_betweeness, geometry='geometry')

        # merge linestrings
        merged_linestrings = gdf_betweeness['geometry'].tolist()
        merged_linestrings = MultiLineString(merged_linestrings)
        merged_linestrings = linemerge(merged_linestrings)
        if type(merged_linestrings) == MultiLineString:
            merged_linestrings = linemerge_sequential(merged_linestrings)
        #print distance_linestring(merged_linestrings)
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

def linestring_between_points(linestring, point_1, point_2):
    # get cut points
    proj_point1 = linestring.interpolate(linestring.project(point_1))
    proj_point2 = linestring.interpolate(linestring.project(point_2))

    # cut linestring given projection point
    inline = cut_line_at_points(linestring, [proj_point1, proj_point2])[1]

    return inline

# split linestring on its point which is the nearest the given point
def split_linestring(point, linestring):
    nearest_point = -1
    shortest_distance = maxint
    for index in range(len(linestring.coords)):
        distance = vincenty(point, linestring.coords[index]).meters
        if distance < shortest_distance:
            shortest_distance = distance
            nearest_point = index

    linestring = list(linestring_s1.coords)

    linestring_slice_1 = linestring[:nearest_point]
    linestring_slice_2 = linestring[nearest_point:]
    print 'len left', len(linestring_slice_1)
    print 'len right', len(linestring_slice_2)

    if len(linestring_slice_1) > 1:
        linestring_slice_1 = LineString(linestring_slice_1)
    elif len(linestring_slice_1) == 1:
        linestring_slice_1 = Point(linestring_slice_1)
    else:
        linestring_slice_1 = []

    if len(linestring_slice_2) > 1:
        linestring_slice_2 = LineString(linestring_slice_2)
    elif len(linestring_slice_2) == 1:
        linestring_slice_2 = Point(linestring_slice_2)
    else:
        linestring_slice_2 = []

    return linestring_slice_1, linestring_slice_2

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

        print 'nearest_linestring_s1', gdf_trunk_line.loc[nearest_linestring_s1]['objectid']
        print 'nearest_linestring_s2', gdf_trunk_line.loc[nearest_linestring_s2]['objectid']

        # get linestrings near stations point
        gdf_trunk_line_s1 = gdf_trunk_line.loc[nearest_linestring_s1]
        gdf_trunk_line_s2 = gdf_trunk_line.loc[nearest_linestring_s2]

        linestring_s1 = gdf_trunk_line_s1['geometry']
        linestring_s2 = gdf_trunk_line_s2['geometry']

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

        else:
            # split linestrings given stops
            edge = linestring_between_points(merged_linestrings, point_s1, point_s2)
            geo_link = link.to_dict()
            geo_link['geometry'] = edge
            geo_link['shape_len'] = distance_linestring(edge)
            list_geolinks.append(geo_link)

            # if stop_1['objectid'].iloc[0] == 375  and stop_2['objectid'].iloc[0] == 394:
            #
            #     # plot edges and points
            #     fig, ax = plt.subplots()
            #     ax.set_aspect('equal')
            #     ax.axis('off')
            #
            #     x, y = merged_linestrings.xy
            #     ax.plot(x,y, color='purple')
            #
            #     x, y = linestring_s1.xy
            #     ax.plot(x,y, color='blue')
            #     x, y = linestring_s2.xy
            #     ax.plot(x,y, color='red')
            #
            #     x, y = edge.xy
            #     ax.plot(x,y, color='green')
            #
            #     x, y = point_s1.xy
            #     ax.scatter(x,y, color='black')
            #     x, y = point_s2.xy
            #     ax.scatter(x,y, color='black')
                #fig.savefig(result_folder + 'path_between_stops.pdf')
                #break

    gdf_geolinks = gpd.GeoDataFrame(list_geolinks, geometry='geometry')
    return gdf_geolinks

def path_between_transitions(df_transition_links, gdf_stations):
    list_geolinks = []
    for index, link in df_transition_links.iterrows():
        # get node position
        stop_1 = gdf_stations[gdf_stations['objectid'] == link['node_1']]
        stop_2 = gdf_stations[gdf_stations['objectid'] == link['node_2']]
        
        # create linestring from stop position
        geo_link = link.to_dict()
        geo_link['geometry'] = LineString([stop_1['geometry'].iloc[0], stop_2['geometry'].iloc[0]])
        geo_link['shape_len'] = distance_linestring(geo_link['geometry'])
        list_geolinks.append(geo_link)

    gdf_geolinks = gpd.GeoDataFrame(list_geolinks, geometry='geometry')
    return gdf_geolinks

'''
    Test area
'''
# preprocessing lines
# gdf_lines = preprocess_lines(gdf_lines)
# print gdf_lines
# gdf_lines.to_file(result_folder + 'splitted_links.shp')

# get links between stations for all subway trunks
list_geolinks = []

# transition links
df_transition_links = df_links[df_links['trunk'] == 'T']
gdf_geolinks_transitions = path_between_transitions(df_transition_links, gdf_stations)
list_geolinks.append(gdf_geolinks_transitions)

list_unique_trunks = gdf_lines['rt_symbol'].unique()
for trunk in list_unique_trunks:
    gdf_lines_trunk = gdf_lines[gdf_lines['rt_symbol'] == trunk]
    gdf_lines_trunk = preprocess_lines(gdf_lines_trunk)
    print 'Trunk:', trunk

    # treat cases when paths intersect others of the same line
    if trunk == 'B':
        # delete unnecessary edge
        gdf_lines_trunk = gdf_lines_trunk[gdf_lines_trunk['id'] != 2000293]

        # create a graph with subway lines
        g_lines = create_line_graph(gdf_lines_trunk)

        # add necessary edge where lines are too far each other
        index_1 = gdf_lines_trunk[gdf_lines_trunk['id'] == 2000292].index.values.tolist()[0]
        index_2 = gdf_lines_trunk[gdf_lines_trunk['id'] == 2000294].index.values.tolist()[0]
        g_lines.add_edge(index_1, index_2, trunk=trunk)

        list_index_1 = gdf_lines_trunk[gdf_lines_trunk['objectid'] == 1281].index.values.tolist()
        index_2 = gdf_lines_trunk[gdf_lines_trunk['objectid'] == 969].index.values.tolist()[0]
        index_3 = gdf_lines_trunk[gdf_lines_trunk['objectid'] == 1349].index.values.tolist()[0]
        for index_1 in list_index_1:
            g_lines.remove_edge(index_1, index_2)
            g_lines.remove_edge(index_1, index_3)

    elif trunk == 'N':
        gdf_lines_trunk = gdf_lines_trunk[gdf_lines_trunk['objectid'] != 1094]

        # create a graph with subway lines
        g_lines = create_line_graph(gdf_lines_trunk)

        index_1 = gdf_lines_trunk[gdf_lines_trunk['objectid'] == 873].index.values.tolist()[0]
        # get edges from index_1
        list_neighbors = g_lines.neighbors(index_1)
        neighbors_tobe_removed = []
        for neighbor in list_neighbors:
            if gdf_lines_trunk.loc[neighbor]['objectid'] == 1809:
                g_lines.remove_edge(index_1, neighbor)
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
