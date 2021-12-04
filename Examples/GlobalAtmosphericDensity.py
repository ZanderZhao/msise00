#!/usr/bin/env python
"""
Function: 计算并绘制全球大气成分及密度的分布
online: https://github.com/ZanderZhao/msise00/blob/main/Examples/GlobalAtmosphericDensity.py
Author: ZanderZhao
"""
import ftplib
import os
from datetime import datetime
import xarray
from matplotlib.pyplot import figure
from pathlib import Path
import msise00 # https://github.com/space-physics/msise00
from msise00.worldgrid import latlonworldgrid
from msise00.plots import writeplot
# debain需要安装 cmake>=3.14  c c++ fortran 编译器

def plot2dlatlon_self(atmos: xarray.Dataset, rodir: Path = None, slat: float = None, slon: float = None):
    """
    绘制经纬度网格的大气成分及密度的分布,改自plot2dlatlon函数,添加Total密度的绘制
    :param atmos: 数据集,必选参数
    :param rodir: 图片保存路径,可选参数,默认当前脚本运行路径
    :param slat: 太阳直射纬度,可选参数
    :param slon: 太阳直射经度,可选参数
    :return: 无返回,保存图片
    """
    atmos = atmos.squeeze()

    fg = figure(figsize=(20, 10))
    ax = fg.subplots(3, 3, sharex=True).ravel()
    fg.suptitle(
        "400km High Global Atmospheric Density \n\nDateTime=" +
        str(atmos.time.values.squeeze())[:-13] +
        f"   alt.(km)={atmos.alt_km.item()}   Ap={atmos.Ap}   F10.7A={atmos.f107s}   F10.7={atmos.f107}   "
    )

    j = 0
    for s in atmos.species:
        a = ax[j]
        hi = a.imshow(
            atmos[s].squeeze(),
            aspect="auto",
            interpolation="none",
            cmap="viridis",
            extent=(atmos.lon[0], atmos.lon[-1], atmos.lat[0], atmos.lat[-1]),
        )

        fg.colorbar(hi, ax=a, format='%.2e')
        # %% sun icon moving
        if slat is not None and slon is not None:
            a.plot(slon, slat, linestyle="none", marker="o", markersize=5, color="w")
        if s != "Total":
            a.set_title(f"Density: {s} (cm^-3)")
        else:
            a.set_title(f"Density: {s} (gm/cm^3)")
        a.set_xlim(-180, 180)
        a.set_ylim(-90, 90)
        a.autoscale(False)
        j += 1

    for k in range(0, 6 + 2, 3):
        ax[k].set_ylabel("latitude (deg)")
    for k in (6, 7, 8):
        ax[k].set_xlabel("longitude (deg)")

    if rodir:
        rodir = Path(rodir).expanduser()
    else:
        rodir = Path("./").expanduser()

    ofn = rodir / (
        f"{atmos.alt_km.item():.1f}_" + str(atmos.time.values.squeeze())[:-13] + ".png"
    )
    writeplot(fg, ofn)


def download_ftp_ap(file_name, local_dir):
    """
    下载ap文件
    :param file_name: 文件名
    :param local_dir: 保存文件夹
    :return:
    """
    host_address = 'ftp.ngdc.noaa.gov'
    online_dir = "STP/GEOMAGNETIC_DATA/INDICES/KP_AP/"
    online_name = file_name  # "kp_ap.fmt" "ream-me.txt" "1932" "2018"
    online_path = online_dir + online_name
    local_dir = local_dir  # "/home/zander/PycharmProjects/nrlmsise-demo/msise00/Examples/"
    local_name = online_name
    local_path = local_dir + local_name
    download_ftp_base(host_address, online_path, local_path)


# file:///run/user/1000/gvfs/ftp:host=ftp.swpc.noaa.gov/pub/indices/old_indices
def download_ftp_f107(file_name, local_dir):
    """
    下载f107文件
    :param file_name: 文件名
    :param local_dir: 保存路径
    :return:
    """
    host_address = 'ftp.swpc.noaa.gov'
    online_dir = "pub/indices/old_indices/"
    online_name = file_name  # "README" 1994-2021  "1994_DGD.txt" "1994_DPD.txt" #"1994_DSD.txt"
    online_path = online_dir + online_name
    local_dir = local_dir  # "/home/zander/PycharmProjects/nrlmsise-demo/msise00/Examples/"
    local_name = online_name
    local_path = local_dir + local_name
    download_ftp_base(host_address, online_path, local_path)


def download_ftp_base(host_address, online_path, local_path):
    """
    从ftp下载文件的基础函数
    :param host_address: ftp主机地址
    :param online_path: 在线的路径,不包括地址
    :param local_path: 本地保存路径
    :return: 保存文件
    """
    with ftplib.FTP(host_address) as ftp:

        file_orig = online_path
        file_copy = local_path

        try:
            ftp.login()

            with open(file_copy, 'w') as fp:
                print("start download from ftp")
                res = ftp.retrlines('RETR ' + file_orig, fp.write)

                res = ftp.retrlines('RETR ' + file_orig, lambda s, w=fp.write: w(s + '\n'))
                # https://geek-docs.com/python/python-tutorial/python-ftp.html
                # https://stackoverflow.com/questions/14224091/how-to-correctly-download-files-using-ftplib-so-line-breaks-are-added-for-window

                if not res.startswith('226 Transfer complete'):

                    print('Download failed')
                    if os.path.isfile(file_copy):
                        os.remove(file_copy)
                print("download sucessful")

        except ftplib.all_errors as e:
            print('FTP error:', e)

            if os.path.isfile(file_copy):
                os.remove(file_copy)


def download_ftp_data_demo():
    """
    下载数据演示
    :return: 成功返回True
    """
    file_name = "2015"
    local_path = "/home/zander/PycharmProjects/nrlmsise-demo/msise00/Examples/"
    download_ftp_ap(file_name, local_path)

    file_name = "2017_DSD.txt"
    local_path = "/home/zander/PycharmProjects/nrlmsise-demo/msise00/Examples/"
    download_ftp_f107(file_name, local_path)
    return True


def gad_run(year_list, img_path="./", nc_path="./",
        t_month=10, t_day=1, t_time=10,
        f107s_list=None, f107_list=None, ap_list=None,
        n_glat=10.0, n_glon=20.0, alt_km=400.0):
    """
    计算全球气体密度分布并绘图 Global Atmospheric Density
    :param year_list: 要计算年份的列表
    :param img_path: 保存图片的路径
    :param nc_path: nc数据保存文件的路径
    :param t_month: 要计算的月份
    :param t_day: 要计算的哪一天
    :param t_time: 哪一天的时间
    :param f107s_list: 这天的F107A 81天平均的F10.7通量,和year_list长度一样的列表
    :param f107_list: F107 前一天的F10.7日通量,和year_list长度一样的列表
    :param ap_list: AP 每日的地磁指数,和year_list长度一样的列表
    :param n_glat: 纬度步长间隔
    :param n_glon: 经度步长间隔
    :param alt_km: 海拔高度,单位千米
    :return: 跑成功任意一个,结果返回True,没有跑成功一个返回False
    """
    glat, glon = latlonworldgrid(n_glat, n_glon)
    result=False
    for num in range(len(year_list)):
        # time = datetime(2021, 10, 1, 10, 0, 0)
        # year_list = [2019, 2018, 2017, 2016, 2015, 2014]  # 年份列表
        time = datetime(year_list[num], t_month, t_day, t_time, 0, 0)

        if f107s_list is None or f107_list is None or ap_list is None:
            atmos = msise00.run(time, alt_km, glat, glon)  # , indices)
        else:
            indices = dict()
            # indices["f107s"] = 85
            indices["f107s"] = f107s_list[num]
            # indices["f107"] = 90
            indices["f107"] = f107_list[num]
            # indices["Ap"] = 7
            indices["Ap"] = ap_list[num]
            atmos = msise00.run(time, alt_km, glat, glon, indices)

        try:
            nc_final_path = os.path.join(nc_path, "400.0_" + str(time.date()) + '.nc')
            save_result = atmos.to_netcdf(nc_final_path)
            # atmos=xarray.open_dataset(str(nc_final_path)
            plot2dlatlon_self(atmos, img_path)
            # show()
            result = True
        except BaseException as e:
            print(e)
    return result

if __name__ == "__main__":
    ### 配置参数
    # 图片保存文件夹
    save_img_path = r"/home/zander/PycharmProjects/nrlmsise-demo/data/img"
    # nc原始数据保存文件夹
    save_nc_path = r"/home/zander/PycharmProjects/nrlmsise-demo/data/nc"

    # 24周期  2008年-2019年
    # 开始计算的年
    start_year=2008
    # 停止计算的年
    end_year=2019
    # 年步长
    delta_year=1
    # # 计算的月
    # t_month=10
    # # 计算的日
    # t_day=1

    ### run
    year_list = list(range(start_year,end_year+1,delta_year))
    gad_run(year_list, img_path=save_img_path, nc_path=save_nc_path)
    # gad_run(year_list, img_path=save_img_path, nc_path=save_nc_path,t_month=t_month,t_day=t_day)

