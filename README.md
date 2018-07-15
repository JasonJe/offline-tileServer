# 离线瓦片地图


## 1. 获取瓦片地图


### 1.1 主要地图瓦片坐标系定义及计算原理

瓦片地图具有如下特点：

* 具有唯一的瓦片等级和瓦片坐标编号；

* 分辨率为 256*256；

* 瓦片等级越高，展示的地图信息约详尽，瓦片数量也越多；

* 上一等级的一张瓦片地图可分割为下一等级的四张瓦片地图。

参考文章：  [《国内主要地图瓦片坐标系定义及计算原理》](https://blog.csdn.net/wudiazu/article/details/76597294)


### 1.2 [pyGeoTile 库](https://github.com/geometalab/pyGeoTile)的使用（计算瓦片地图坐标）

GitHub: https://github.com/geometalab/pyGeoTile

安装：`pip install pygeotile`

```
from pygeotile.tile import Tile

lon, lat = 109.227, - 20.196
zoom = 12

tile = Tile.for_latitude_longitude(latitude = lat, longitude = lon, zoom = zoom)
print('mintile', 'X:', tile.tms_x, 'Y:', tile.tms_y, 'zoom:', tile.zoom)
```


### 1.3 多进程/多线程/异步爬取瓦片地图

* 高德瓦片地图链接：http://wprd03.is.autonavi.com/appmaptile?style=7&x={x}&y={y}&z={z}

* 谷歌瓦片地图链接：http://mt2.google.cn/vt/lyrs=m@167000000&hl=zh-CN&gl=cn&x={x}&y={y}&z={z}&s=Galil

三种方式爬取等级12瓦片地图（6164张图片）的效率对比

爬取方式：使用时间(秒)

* 多进程：24.49594s

* 多线程：16.11365s

* 异步：14.01809s


## 2. Flask + Leaflet 瓦片地图


### 2.1 瓦片地图路由定义

```
@app.route("/tile")
def tile():
    x = request.args['x']
    y = request.args['y']
    z = request.args['z']
    with open('./tilefile/%s/%s_%s.png'%(z, x, y), 'rb') as f:
        image = f.read()
    return Response(image, mimetype='image/jpeg')
```

* 瓦片地图接口 url: /tile?x={x}&y={y}&z={z}


### 2.2 [Leaflet 地图库](https://leafletjs.com/) 使用

GitHub：https://github.com/Leaflet/Leaflet

```
var url = '/tile?x={x}&y={y}&z={z}';


var latlng = new L.latLng(23.461, 111.921);
var map = new L.map('mapDiv', {
	center: latlng,
	zoom:  4,
	detectRetina: true
});

L.tileLayer(url).addTo(map);
```