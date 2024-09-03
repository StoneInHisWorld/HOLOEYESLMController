# HOLOEYE SLM CONTROLLER v1.0
根据官方编程示例编写的HOLOEYE™ SLM的控制程序

## 使用之前
需要引入随包装附赠的HOLOEYE™ SLM Display SDK：
1. 在使用的环境目录下添加`./holoeye`文件夹
2. `holoeye`文件夹位于`your/directory/HOLOEYE Photonics/SLM Display SDK (Python) v_your_version_/python`
3. 添加目录为：`your/directory/envs/your_env/Lib/site-packages`

## ./holoeye_dependency
`./holoeye_dependency`目录负责存放HOLOEYE™ 编程示例，至少需要在`./holoeye_dependency`中加入官方编程示例`showSLMPreview.py`。
**请从安装的SDK中附带的目录`SLM Display SDK (Python) v_your_version_ Examples`中获取**


## `from HoloeyeSLMController import HoloeyeSLM as SLM`
Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能：
1. `open_preview()`：打开SLM预览界面，以便实验调试。
2. `present()`：向SLM展示单份数据。
3. `AS_show()`：通过多线程控制异步地展示数据。
4. `size`：获取SLM的高宽