# HOLOEYE SLM CONTROLLER v1.1
根据官方编程示例编写的HOLOEYE™ SLM的控制程序

## 使用之前
需要引入随包装附赠的HOLOEYE™ SLM Display SDK，安装SDK后需要重启电脑以使环境变量生效：
1. 在使用的环境目录下添加`./holoeye`文件夹
2. `holoeye`文件夹位于`{your/directory}/HOLOEYE Photonics/SLM Display SDK (Python) v{_your_version_}/python`
3. 添加目录为：`{your/directory}/envs/{your_env}/Lib/site-packages`

## ./holoeye_dependency
`./holoeye_dependency`目录负责存放HOLOEYE™ 编程示例，至少需要在`./holoeye_dependency`中加入官方编程示例`showSLMPreview.py`。
**请从安装的SDK中附带的目录`SLM Display SDK (Python) v_your_version_ Examples`中获取**

## `from HoloeyeSLMController import HoloeyeSLM as SLM`
Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能：
1. `open_preview()`：打开SLM预览界面，以便实验调试。
2. `present()`：向SLM展示单份数据。
3. `AS_show()`：通过多线程控制异步地展示数据。
4. `size`：获取SLM的高宽

## 编程范例
异步展示数据

```python
from holoeyeslm_op import HoloeyeSLM
import threading
import queue
import os
import numpy as np

# 设置SLM参数
rise_time = 0.1
slm_preview = False

with HoloeyeSLM(rise_time) as slm:
    # 通信信号设置
    start_signal = threading.Event()
    end_signal = threading.Event()
    pending_pics = queue.Queue(1)

    # 开启SLM
    path_generator = lambda i: os.path.join('./', f'{str(i)}.jpg')
    slm_thread = threading.Thread(
        target=slm.async_present,
        args=(
            np.random.randn(100, 100, 100),
            start_signal, end_signal, pending_pics,
            slm_preview, None, path_generator
        )
    )
    # 开启其他设备
    slm_thread.start()
    start_signal.set()
    end_signal.wait()
```

同步展示数据

```python
import numpy as np

from holoeyeslm_op import HoloeyeSLM

# 设置SLM参数
rise_time = 0.1
slm_preview = False

with HoloeyeSLM(rise_time) as slm:
    for file in np.random.randn(100, 100, 100):
        slm.syn_present(file)
```