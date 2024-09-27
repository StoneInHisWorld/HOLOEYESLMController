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
from queue import Queue
from threading import Event
from typing import Iterable, Callable

import numpy
from holoeye import slmdisplaysdk
from tqdm import tqdm
from ..holoeye_dependency.showSLMPreview import showSLMPreview


class HoloeyeSLM:
    """Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能"""

    def __init__(self, rise_time=0.01):
        """Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能

        :param rise_time: SLM的上升时间，根据实验实际进行设置，以解决设备同步问题。
        """
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
        """通过官方示例showSLMPreview()打开SLM预览界面

        若需要指定pos参数，请进入showSLMPreview.py进行有关pos参数的编程，并修改接口。
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

    def syn_present(self, file, showFlag=slmdisplaysdk.ShowFlags.PresentAutomatic):
        """向SLM展示单份数据。

        如果是字符串，则认定为文件路径名；如果是numpy多维数组，则直接进行展示。
        :param file: 要展示的数据
        :param showFlag: 展示模式
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
            raise NotImplementedError(
                f"不支持的文件类型{type(file)}！file参数可以传递的数据类型为字符串（指示数据路径）以及numpy多维数组。")
        time.sleep(self.rise_time)
        assert error == slmdisplaysdk.ErrorCode.NoError, slm.errorString(error)

        # 如果在脚本运行完成后，IDE中止了python解释器进程，则SLM上的内容会随着脚本的运行结束而消失

    def async_present(self,
                      files: Iterable, start_signal: Event, end_signal: Event,
                      pending_pics: Queue = None, preview_window=False, present_interval: float = None,
                      file_transformer: Callable = None, path_generator: Callable = None,
                      preview_kwargs=None, show_kwargs=None
                      ):
        """多线程异步展示数据

        :param files: 要展示的图片文件列表
        :param start_signal: 数据展示开始事件。
            作为所有设备开始工作的同步信号，在检查该事件之前，将会完成SLM的初始化工作。
        :param end_signal: 数据展示结束事件。
            数据展示完毕，本设备会将其set，从而通知所有设备展示已经完成。
        :param pending_pics: 数据保存路径输送队列。
            展示一份数据后，会调用路径生成器`path_generator`生成该份数据的保存路径（该保存路径可以包含有数据的编号），
            放入该队列中。队列中的路径作为信号发布给所有持有该队列的设备。
            设置为None则会进行连续展示模式。
        :param preview_window: 是否打开SLM预览窗
        :param present_interval: 连续展示下，数据间的展示间隔，设置为None则会进行无间断展示。
        :param file_transformer: 文件展示前，需要进行的预处理程序，签名需为：
            def file_transformer(file) -> file
            其中，file为单张图片。
        :param path_generator: 路径生成器，负责生成每张图片的保存路径，签名需为：
            def path_generator(i) -> PathlikeObj
            其中，i为图片编号。
        :param preview_kwargs: 图片预览关键字参数，为self.open_preview()的关键字参数。
        :param show_kwargs: 图片展示关键字参数，为self.present()的关键字参数。
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
                # 等待设备处理完上个文件
                if pending_pics:
                    pending_pics.join()
                # 展示文件
                self.syn_present(file, **show_kwargs)
                if present_interval:
                    time.sleep(present_interval)
                # 将文件存储路径放入队列并通知设备处理
                if pending_pics:
                    pending_pics.put_nowait(path_generator(i))
        end_signal.set()

    @property
    def size(self):
        return (self.__device.height_px, self.__device.width_px)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__device = None
