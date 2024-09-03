# HOLOEYE SLM CONTROLLER v1.0
根据官方编程示例编写的HOLOEYE™ SLM的控制程序

## `from HoloeyeSLMController import HoloeyeSLM as SLM`
Holoeye™ SLM控制器，集成了在Holoeye™ SLM上展示图片的各种功能：
1. `open_preview()`：打开SLM预览界面，以便实验调试。
2. `present()`：向SLM展示单份数据。
3. `AS_show()`：通过多线程控制异步地展示数据。
4. `size`：获取SLM的高宽