#!/usr/bin/env python
# coding: utf-8

import io
import os
import gc
import time
import pdf2image
import asyncio
import traceback
import matplotlib
matplotlib.use('PDF')

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import shapely.geometry

from PIL import Image
from shapely import geos
from pygeotile.point import Point
from pygeotile.tile import Tile
from fiona.crs import from_epsg,from_string

shp_file     = './data/shp.shp'
base_file    = './data/base.shp'
plt_dpi      = 72
min_zoom     = 16
max_zoom     = 16

Image.MAX_IMAGE_PIXELS = 10 ** 12

plt.rcParams['font.sans-serif']    = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi']         = plt_dpi

def genrate_im(base_df, bounds_df, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, fontsize = 18, plt_dpi = plt_dpi):
    fig, ax = plt.subplots()
    plt.axis('off')
    
    base_map = base_df.plot(
                    ax        = ax,
                    alpha     = 0.6, 
                    edgecolor = 'black',
                    color     = 'w',
                    figsize   = ((maxtms_x - mintms_x + 1) * 256 / plt_dpi, 
                                  (maxtms_y - mintms_y + 1) * 256 / plt_dpi)
                )

    bounds_df.plot(ax = base_map, color = 'w', markersize = 1, alpha = 0.1, edgecolor = 'gray')

    for idx, row in base_df.iterrows():
        plt.annotate(s  = row['MC'] ,
                     xy = row['coords'],
                     horizontalalignment = 'center',
                     fontsize = fontsize,
                     color    = 'black')
    if zoom >= 12:
        for idx, row in bounds_df.iterrows():
            if row['MC'] is None:
                continue
            if  '争议地' in row['MC']:
                continue
            if  '飞地' in row['MC']:
                continue
            if '(海域)' in row['MC']:
                continue
            plt.annotate(s  = row['MC'] ,
                         xy = row['coords'],
                         horizontalalignment = 'center',
                         fontsize = 8,
                         color    = 'black')
    
    fig.set_size_inches((maxtms_x - mintms_x + 1) * 256 / plt_dpi, 
                        (maxtms_y - mintms_y + 1) * 256 / plt_dpi)

    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1,bottom=0,left=0,right=1,hspace=0,wspace=0)
    plt.margins(0,0)

    buf = io.BytesIO()
    plt.savefig(buf, format = 'pdf', bbox_inches='tight', dpi= plt_dpi, pad_inches = 0)
    buf.seek(0)
    
    im = pdf2image.convert_from_bytes(buf.read())[0]
    im = im.convert('L')
    im = im.resize(((maxtms_x - mintms_x + 1) * 256, (maxtms_y - mintms_y + 1) * 256))
    
    return im

async def genrate_tile_position(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path):
#def genrate_tile_position(mintms_x, maxtms_x, mintms_y, maxtms_y, zoom):
    for idx_x, x in enumerate(range(mintms_x, maxtms_x + 1)):
        for idx_y, y in enumerate(range(mintms_y, maxtms_y + 1)):
            #yield (idx_x, idx_y, x, y, zoom)
            position = (idx_x, idx_y, x, y, zoom)
            await crop_image(im, position, x, y, zoom, save_path) 

async def crop_image(im, position, x, y, zoom, save_path):
    temp_im = im.crop((256 * position[0], 256 * position[1], 256 * (position[0] + 1), 256 * (position[1] + 1)))
    print("----- tile save in {}".format(os.path.join(save_path, '{}_{}_{}.png'.format(x, y, zoom))))
    temp_im.save(os.path.join(save_path, '{}_{}_{}.png'.format(x, y, zoom)))
    del im
    del temp_im
    gc.collect()

async def genrate_tile(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path):
    print(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path)
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    await genrate_tile_position(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path)
    #for tile_position in genrate_tile_position(mintms_x, maxtms_x, mintms_y, maxtms_y, zoom):
    #    print(tile_position)
    #    print("-----------{} {} {} -----".format(zoom, tile_position[2], tile_position[3]))
    #    #position = (256 * idx_x, 256 * idx_y, 256 * (idx_x + 1), 256 * (idx_y + 1))
    #    position  = tile_position
    #    await crop_image(im, position, tile_position[2], tile_position[3], zoom, save_path)
    del im 
    gc.collect()

#async def handler(im_list): # python 3.7 support
#    #tasks = [asyncio.create_task(genrate_tile(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path)) for im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path in im_list]
#    taskd = []
#    for im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path in im_list:
#        tasks.append(asyncio.create_task(genrate_tile(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path)))
#        del im
#    await asyncio.gather(*tasks)
    
def main():
    shp_df     = gpd.GeoDataFrame.from_file(shp_file, encoding = 'utf-8')
    base_df    = gpd.GeoDataFrame.from_file(base_file, encoding = 'utf-8')

    base_df['coords']  = base_df['geometry'].apply(
            lambda x: x.representative_point().coords[:]
        )
    base_df['coords']  = [coords[0] for coords in base_df['coords']]
    shp_df['coords']  = shp_df['geometry'].apply(
            lambda x: x.representative_point().coords[:]
        )
    shp_df['coords']  = [coords[0] for coords in shp_df['coords']]
    
    im_list = []
    for zoom in range(min_zoom, max_zoom + 1):
        print("----- genrate {} image -----".format(zoom))
        right_buttom_tile  = Tile.for_latitude_longitude(latitude = -22.380080, longitude = 115.425220, zoom = zoom)
        left_top_tile      = Tile.for_latitude_longitude(latitude = -23.966600, longitude = 113.816970, zoom = zoom)

        mintms_x, mintms_y = left_top_tile.tms_x, left_top_tile.tms_y
        maxtms_x, maxtms_y = right_buttom_tile.tms_x, right_buttom_tile.tms_y

        im = genrate_im(base_df, shp_df, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, fontsize = 18, plt_dpi = plt_dpi)

        save_path = "./tile/tile_{}".format(zoom)
        im_list.append((im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path))
        print("----- end {} -----".format(zoom))
    
    del base_df 
    del shp_df
    gc.collect()

    start = time.perf_counter()
    loop = asyncio.get_event_loop()
    print("----- start -----")
    tasks = []
    for im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path in im_list:
        print("------------------------")
        #task = loop.create_task(genrate_tile(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path))
        tasks.append(asyncio.ensure_future(genrate_tile(im, mintms_x, maxtms_x, mintms_y, maxtms_y, zoom, save_path)))
        print("---- end ----")
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()
    # asyncio.run(handler(im_list)) # python 3.7 support
    print("Cost {} s".format(time.perf_counter() - start))

if __name__ == '__main__':
    main()

