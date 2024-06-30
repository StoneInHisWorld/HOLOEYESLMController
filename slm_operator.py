# -*- coding: utf-8 -*-

#--------------------------------------------------------------------#
#                                                                    #
# Copyright (C) 2023 HOLOEYE Photonics AG. All rights reserved.      #
# Contact: https://holoeye.com/contact/                              #
#                                                                    #
# This file is part of HOLOEYE SLM Display SDK.                      #
#                                                                    #
# You may use this file under the terms and conditions of the        #
# "HOLOEYE SLM Display SDK Standard License v1.0" license agreement. #
#                                                                    #
#--------------------------------------------------------------------#


import os
import time
from multiprocessing import Event, Queue
# import dill
import numpy
# 引入SLM Display SDK:
# 请在使用的环境目录下添加holoeye文件夹
# 使用的环境目录：~/envs/your_env/Lib/site-packages
# holoeye文件夹位于~/HOLOEYE Photonics/SLM Display SDK (Python) v_your_version_/python
from holoeye import slmdisplaysdk
from tqdm import tqdm
# holoeye_dependency请从安装的SDK中附带的SLM Display SDK (Python) v_your_version_ Examples中获取
# 至少需要在holoeye_dependency中加入showSLMPreview.py
from holoeye_dependency.showSLMPreview import showSLMPreview


class HoloeyeSLM:

    def __init__(self, rise_time=0.01):
        """Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能。"""
        # 初始化SLM库
        self.__device = slmdisplaysdk.SLMInstance()
        self.rise_time = rise_time

        # 检查库是否实现了所需版本
        if not self.__device.requiresVersion(5):
            exit(1)

        # 检测SLM并打开所选SLM窗口
        error = self.__device.open()
        assert error == slmdisplaysdk.ErrorCode.NoError, self.__device.errorString(error)

    def __enter__(self):
        return self

    def open_preview(self, scale=0., showFlag=0, pos=None):
        """
        打开SLM预览界面
        :param scale: 设置为0.0时，为“Fit”模式；设置为1.0时，屏幕的一个像素对应SLM的一个像素。
            请注意下采样插值会让数据看起来完全不一样。
        :param showFlag: 展示标记。
            不使用任何设置：NoFlag = 0；
            去除预览窗口的界限：NoBorder = 1
            保证预览窗口始终置顶（被注意）：OnTop = 2
            展示Zernike半径：ShowZernikeRadius = 4
            在预览窗口展示波前补偿：ShowWavefrontCompensation = 8
        :param pos: 窗口参量(x, y, w, h)。x、y表示屏幕坐标，w、h表示窗口宽高。
            若窗口不翼而飞，请将此参数设置为None。
        :return: None
        """
        showSLMPreview(self.__device, scale, showFlag)

    def present(self, file, showFlag=slmdisplaysdk.ShowFlags.PresentAutomatic):
        """向SLM展示数据。
        如果是字符串，则认定为文件路径名；如果是numpy多维数组，则直接进行展示。
        :param file: 要展示的数据
        :param showFlag: 展示模式
        :return: None
        """
        slm = self.__device

        # 在SLM上展示文件
        if isinstance(file, str):
            # 如果是字符串，则认定为文件路径名
            error = slm.showDataFromFile(file, showFlag)
        elif isinstance(file, numpy.ndarray):
            # 如果是numpy多维数组，则直接进行展示
            error = slm.showData(file, showFlag)
        else:
            # 否则出错
            raise NotImplementedError(f"不支持的文件类型{type(file)}！file参数可以传递的数据类型为字符串（指示数据路径）以及numpy多维数组。")
        time.sleep(self.rise_time)
        assert error == slmdisplaysdk.ErrorCode.NoError, slm.errorString(error)

        # 如果在脚本运行完成后，IDE中止了python解释器进程，则SLM上的内容会随着脚本的运行结束而消失

    def AS_show(self, files, 
                start_signal, end_signal, pending_pics, 
                preview_window=False, file_transformer=None, path_generator=None,
                preview_kwargs=None, show_kwargs=None
                ):
        """多线程异步展示数据
        :param files:
        :param file_transformer:
        :param end_signal:
        :param preview_kwargs:
        :param show_kwargs:
        :return: None
        """
        # 设置初始参数
        if preview_kwargs is None:
            preview_kwargs = {}
        if show_kwargs is None:
            show_kwargs = {}
        if file_transformer is None:
            file_transformer = lambda f: f
        if path_generator is None:
            path_generator = lambda i: os.path.join(f'{str(i)}.jpg')
        # 打开预览窗口
        if preview_window:
            self.open_preview(**preview_kwargs)
        # 展示待展示图片
        with tqdm(files, desc='\r展示图片……', unit='张',
                  mininterval=1, position=0, leave=True) as pbar:
            start_signal.wait()
            for i, file in enumerate(pbar):
                file = file_transformer(file)
                # 等待相机处理完上个文件
                pending_pics.join()
                # 展示文件
                self.present(file, **show_kwargs)
                # time.sleep(0.5)
                # 将文件存储路径放入队列并通知相机拍照
                pending_pics.put_nowait(path_generator(i))
        end_signal.set()

    def AS_show_p(self, files, 
                  start_signal: Event, pending_pics: Queue, saved: Event,
                  preview_window=False, file_transformer=None, path_generator=None,
                  preview_kwargs=None, show_kwargs=None
                  ):
        """多进程异步展示数据
        :param files:
        :param file_transformer:
        :param end_signal:
        :param preview_kwargs:
        :param show_kwargs:
        :return: None
        """
        # TODO: FATAL ERROR HOLOEYE SLM不支持多进程编程
        # 设置初始参数
        if preview_kwargs is None:
            preview_kwargs = {}
        if show_kwargs is None:
            show_kwargs = {}
        if file_transformer is None:
            file_transformer = lambda f: f
        # else:
        #     file_transformer = dill.loads(file_transformer)
        if path_generator is None:
            path_generator = lambda i: os.path.join(f'{str(i)}.jpg')
        # else:
        #     path_generator = dill.loads(path_generator)
        # 打开预览窗口
        if preview_window:
            self.open_preview(**preview_kwargs)
        start_signal.set()
        saved.set()
        # 展示待展示图片
        with tqdm(files, desc='\r展示图片……', unit='张',
                  mininterval=1, position=0, leave=True) as pbar:
            for i, file in enumerate(pbar):
                file = file_transformer(file)
                # 等待相机处理完上个文件
                saved.wait()
                # 展示文件
                self.present(file, **show_kwargs)
                saved.clear()
                # time.sleep(1)
                # 将文件存储路径放入队列并通知相机拍照
                pending_pics.put(path_generator(i))
        

    @property
    def size(self):
        return (self.__device.height_px, self.__device.width_px)


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__device = None


