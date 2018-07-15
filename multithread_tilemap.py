## 多线程爬取切片地图
from pygeotile.tile import Tile
from urllib import request
import os
import time
from multiprocessing import Pool, TimeoutError, Queue
import threading

global start_time
start_time = time.time()

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

        global imagelists
        imagelists = Queue()
        for x in range(mintms_x, maxtms_x + 1):
            for y in range(maxtms_y, mintms_y + 1):
                savepath = './%s/%d/%d_%d.png'%(rootpath, zoom, x, y)
                tileurl = basetileurl + '&x=%d&y=%d&z=%d'%(x, y, zoom)
                imagelists.put((tileurl, savepath))

        return imagelists

def save_image(imagelists):
    while True:
        try:
            print('---- Length', imagelists.qsize())
            if imagelists.empty():
                print("Done!")
                global used_time
                used_time = time.time() - start_time
                print('---- Used time: ', used_time)
                break
            image = imagelists.get()
            tileurl, savepath = image[0], image[1]
            request.urlretrieve(tileurl, savepath)
            print('---- PID:', os.getpid(), tileurl)
        except Exception as e:
            print('---- Error: {}'.format(e))
            with open('./error.log', 'a') as f:
                f.write('---- Error: {}'.format(e))

def main():
    minlon, minlat = 109.227, - 20.196 # 矩形区域左下角坐标
    maxlon, maxlat = 117.182, - 25.5 # 矩形区域右上角坐标
    minzoom, maxzoom = 12, 12

    basetileurl = 'http://webrd02.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8'
    # basetileurl = 'http://mt2.google.cn/vt/lyrs=m&hl=zh-CN&gl=cn&x=%d&y=%d&z=%d'%(x, y, zoom)
    # basetileurl = 'http://wprd04.is.autonavi.com/appmaptile?lang=zh_cn&size=1&style=7&x=%d&y=%d&z=%d&scl=1&ltype=11'%(x, y, zoom)
    rootpath = './tilefile'

    global threadNum
    threadNum = 10

    imagelists = create_image_url(minlon, minlat, maxlon, maxlat, minzoom, maxzoom, basetileurl, rootpath)
    print('---- Init size', imagelists.qsize())
    for i in range(threadNum):
        td = threading.Thread(target = save_image, args = (imagelists, ))
        td.start()
    td.stop()
    
if __name__ == '__main__':
    main()
