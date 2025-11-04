## Setup x265 software encoder 
   
   https://bitbucket.org/multicoreware/x265_git/src/4.1/
   
   ```sh
  # 1. 克隆x265的git代码仓库
  git clone https://bitbucket.org/multicoreware/x265_git.git
  
  # 2. 进入x265代码目录
  cd x265_git
  
  # 3. 切换到指定的4.1版本
  git checkout 4.1
  
  # 4. 进入源码目录
  cd source
  
  # 5. 使用CMake生成编译配置
  cmake ../source
  
  # 6. 执行编译
  make
  
  # 7. (验证) 检查编译生成的x265版本
  # 编译成功后，在当前目录(source)下会有一个名为 "x265" 的可执行文件
  ./x265 --version
   ```

## Setup Libvmaf software to perform PSNR calculations 

   https://github.com/Netflix/vmaf/tree/v3.0.0/libvmaf

   ```sh
  # 1. 
  git clone https://github.com/Netflix/vmaf.git
  
  # 2. 进入VMAF代码目录
  cd vmaf
  
  # 3. 切换到指定的v3.0.0版本
  git checkout v3.0.0
  
  # 4. 进入libvmaf子目录
  cd libvmaf
  
  # 5. 使用meson和ninja进行编译和安装
  # sudo apt-get install meson ninja-build
  meson build --buildtype release
  ninja -vC build install
  
  build/tools/vmaf -r <reference_video.yuv> -d <distorted_video.yuv> -w <width> -h <height> -p 420 -b 8 --json --threads=1 --output metrics.json --feature psnr
   ```

## Copy 8-bit video sequences to your local machine 
   
   ```sh
   # 1. 创建一个用于存放视频序列的本地目录
   mkdir -p ~/thesis_videos
  
   # 2. 从共享服务器路径复制视频文件到本地
   cp /SHARED_FILES/transfer/stud/reddy/Shang_MA/*.yuv ~/thesis_videos/
  
   # 3. 同时复制包含视频信息的 .yaml 配置文件
   cp /SHARED_FILES/transfer/stud/reddy/Shang_MA/video_sequences_8bit_properties_AOMCTC.yaml ~/thesis_videos/   ```
   ```

## x265 command to do All-Intra encoding with x265 encoder

All-Intra Encoding:`--keyint, -I <integer>` `--keyint 1` All-Intra  
Constant QP Coding:`--qp, -q <integer>`

Rate control -CQP

Code configm -All intra

QP_VALUES = [22, 27, 32, 37]

```sh
x265 \
  --input ControlledBurn_1280x720p30_420.yuv \
  --input-res 1280x720 \
  --fps 30 \
  --frames 129 \
  --intra --keyint 1 --min-keyint 1 --bframes 0 --scenecut 0 \
  --qp <QP> --no-opt-qp-pps --ipratio 1.0 \
  -o output.265
```

lab pc cpu：
[or16ixuv@lms41-30 ~]$ lscpu
| 项目                    | 内容                                            |
| --------------------- | --------------------------------------------- |
| **架构 (Architecture)** | x86_64（64 位 Intel 架构）                         |
| **型号 (Model name)**   | **Intel(R) Core(TM) i5-10505 CPU @ 3.20 GHz** |
| **厂商 (Vendor ID)**    | GenuineIntel                                  |
| **物理核心数**             | 6                                             |
| **每核线程数**             | 1（表示 **超线程关闭/禁用**）                            |
| **逻辑核心总数**            | 6                                             |
| **主频范围**              | 0.8 GHz – 4.6 GHz                             |
| **三级缓存 (L3)**         | 12 MB                                         |
| **二级缓存 (L2)**         | 1.5 MB（6 × 256 KB）                            |
| **一级缓存 (L1d + L1i)**  | 各 192 KB（6 × 32 KB）                           |
| **虚拟化支持**             | ✅ VT-x                                        |
| **NUMA节点数**           | 1（单路CPU）                                      |
