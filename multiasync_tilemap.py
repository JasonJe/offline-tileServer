## 异步爬取切片地图
from pygeotile.tile import Tile
from urllib import request
import os
import asyncio
import time
from time import sleep
from asyncio import Queue
import functools

def create_image_path(rootpath, level):
    path = './%s/%d'%(rootpath, level)
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def create_image_url(minlon, minlat, maxlon, maxlat, minzoom, maxzoom, basetileurl, rootpath):
    for zoom in range(minzoom, maxzoom + 1):
        mintile = Tile.for_latitude_longitude(latitude = minlat, longitude = minlon, zoom = zoom)
        maxtile = Tile.for_latitude_longitude(latitude = maxlat, longitude = maxlon, zoom = zoom)

        print('mintile', 'X:', mintile.tms_x, 'Y:', mintile.tms_y, 'zoom:', mintile.zoom)
        print('maxtile', 'Y:', maxtile.tms_x, 'Y:', maxtile.tms_y, 'zoom:', maxtile.zoom)

        mintms_x, mintms_y = mintile.tms_x, mintile.tms_y
        maxtms_x, maxtms_y = maxtile.tms_x, maxtile.tms_y

        create_image_path(rootpath, zoom)

        imagelists = Queue()
        for x in range(mintms_x, maxtms_x + 1):
            for y in range(maxtms_y, mintms_y + 1):
                savepath = './%s/%d/%d_%d.png'%(rootpath, zoom, x, y)
                tileurl = basetileurl + '&x=%d&y=%d&z=%d'%(x, y, zoom)
                imagelists.put_nowait((tileurl, savepath))

        return imagelists

async def save_image(imagelists):
    while True:
        try:
            start = time.time()
            print('---- Length', imagelists.qsize())
            if imagelists.empty():
                print("Done!")
                break
            image = await imagelists.get()
            tileurl, savepath = image[0], image[1]

            request.urlretrieve(tileurl, savepath)
            print('---- PID:', os.getpid(), '--- use time: ', str(time.time() - start), tileurl)

            imagelists.task_done()
        except Exception as e:
            print('---- Error: {}'.format(e))
            with open('./error.log', 'a') as f:
                f.write('---- Error: {}'.format(e))

def create_image_url_v2(minlon, minlat, maxlon, maxlat, minzoom, maxzoom, basetileurl, rootpath):
    for zoom in range(minzoom, maxzoom + 1):
        mintile = Tile.for_latitude_longitude(latitude = minlat, longitude = minlon, zoom = zoom)
        maxtile = Tile.for_latitude_longitude(latitude = maxlat, longitude = maxlon, zoom = zoom)

        print('mintile', 'X:', mintile.tms_x, 'Y:', mintile.tms_y, 'zoom:', mintile.zoom)
        print('maxtile', 'Y:', maxtile.tms_x, 'Y:', maxtile.tms_y, 'zoom:', maxtile.zoom)

        mintms_x, mintms_y = mintile.tms_x, mintile.tms_y
        maxtms_x, maxtms_y = maxtile.tms_x, maxtile.tms_y

        create_image_path(rootpath, zoom)

        imagelists = []
        for x in range(mintms_x, maxtms_x + 1):
            for y in range(maxtms_y, mintms_y + 1):
                savepath = './%s/%d/%d_%d.png'%(rootpath, zoom, x, y)
                tileurl = basetileurl + '&x=%d&y=%d&z=%d'%(x, y, zoom)
                imagelists.append((tileurl, savepath))

        return imagelists

async def save_image_v2(url):
    tileurl, savepath = url[0], url[1]
    loop = asyncio.get_event_loop()
    try:
        response = await loop.run_in_executor(None, functools.partial(request.urlretrieve, url = tileurl, filename = savepath))
        print('---- PID:', os.getpid(), tileurl)
    except Exception as e:
        print(e)

def main():
    minlon, minlat = 109.227, - 20.196 # 矩形区域左下角坐标
    maxlon, maxlat = 117.182, - 25.5 # 矩形区域右上角坐标
    minzoom, maxzoom = 12, 12

    basetileurl = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8'
    # basetileurl = 'http://mt2.google.cn/vt/lyrs=m&hl=zh-CN&gl=cn&x=%d&y=%d&z=%d'%(x, y, zoom)
    # basetileurl = 'http://wprd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=7&x=%d&y=%d&z=%d&scl=1&ltype=11'%(x, y, zoom)
    rootpath = './tilefile'

    imagelists = create_image_url_v2(minlon, minlat, maxlon, maxlat, minzoom, maxzoom, basetileurl, rootpath)

    tasks = [asyncio.ensure_future(save_image_v2(url)) for url in imagelists]
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

if __name__ == '__main__':
    main_start = time.time()
    main()
    print('---- All time: ', time.time() - main_start)
