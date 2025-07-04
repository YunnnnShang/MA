## Setup x265 software encoder 编译 x265 软件编码器 (v4.1)
   
   https://bitbucket.org/multicoreware/x265_git/src/4.1/
   
   目标: 编译生成版本号为4.1的x265可执行文件，用于软件编码实验。

   行动项:  打开Linux终端，使用git克隆指定的代码仓库。进入仓库目录后，使用 git checkout 4.1 命令，切换到指定的 4.1 版本。这一点很重要，可以确保你的实验结果与助教的预期环境一致。
   
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

## Setup Libvmaf software to perform PSNR calculations 编译并测试 VMAF 库 (v3.0.0)

   https://github.com/Netflix/vmaf/tree/v3.0.0/libvmaf

   目标: 准备用于计算视频质量（PSNR）的工具。

   行动项: 克隆VMAF代码仓库，并使用 git checkout v3.0.0 切换到指定的 v3.0.0 版本。 安装编译所需的工具 meson 和 ninja
   ```sh
  # 1. 克隆VMAF的代码仓库
  git clone https://github.com/Netflix/vmaf.git
  
  # 2. 进入VMAF代码目录
  cd vmaf
  
  # 3. 切换到指定的v3.0.0版本
  git checkout v3.0.0
  
  # 4. 进入libvmaf子目录
  cd libvmaf
  
  # 5. 使用meson和ninja进行编译和安装
  # (如果系统未安装，请先执行: sudo apt-get install meson ninja-build)
  meson build --buildtype release
  ninja -vC build install
  
   ```

   你现在还没有编码失真后的视频（distorted video），所以请将这条命令保存好。等你用x265成功编码出第一个视频后，就可以用它来计算PSNR值，验证整个流程。
   ```
   # 保存此命令备用
   build/tools/vmaf -r <reference_video.yuv> -d <distorted_video.yuv> -w <width> -h <height> -p 420 -b 8 --json --threads=1 --output metrics.json --feature psnr
   ```

## Copy 8-bit video sequences to your local machine 准备测试视频序列

   目标: 将用于实验的原始视频文件复制到本地工作目录。

   行动项: 访问你学校服务器的共享路径 /SHARED_FILES/transfer/stud/reddy/Shang_MA。将该目录下的所有 _8bit_ 视频文件全部复制到你本地PC的工作目录中。找到并用文本编辑器打开 video_sequences_8bit_properties_AOMCTC.yaml 文件。.

   提示: 创建一个简单的笔记或Excel表格，将每个视频序列的文件名与其对应的分辨率、帧率记录下来。这个信息在后续编写自动化脚本和执行命令时至关重要。
   
   ```sh
   # 1. 创建一个用于存放视频序列的本地目录
   mkdir -p ~/thesis_videos
  
   # 2. 从共享服务器路径复制视频文件到本地
   # 注意：请确保你有权限访问该目录，并根据实际情况调整路径
   cp /SHARED_FILES/transfer/stud/reddy/Shang_MA/*.yuv ~/thesis_videos/
  
   # 3. 同时复制包含视频信息的 .yaml 配置文件
   cp /SHARED_FILES/transfer/stud/reddy/Shang_MA/video_sequences_8bit_properties_AOMCTC.yaml ~/thesis_videos/   ```
   ```

## x265核心编码参数命令示例

Find the appropriate command line parameters to do All-Intra encoding with x265 encoder.Following that, parameters to do constant QP coding. 

目标: 掌握用于“全帧内编码”和“固定QP编码”的核心命令行参数。

行动项: 全帧内编码 (All-Intra Encoding):通过查阅x265文档，可以找到`--keyint, -I <integer>`这个参数。 当设置`--keyint 1`时，x265会强制将每一帧都编码为I帧，从而实现All-Intra编码 。 固定QP编码 (Constant QP Coding): 查阅文档可以找到`--qp, -q <integer>`参数。 使用此参数将启用固定QP的码率控制模式 。例如，`--qp 22`会使编码器以恒定的量化参数22来处理视频。
```sh
# 示例：对一个1920x1080, 30fps的视频进行“全帧内”和“固定QP”编码

# 变量定义 (请根据实际视频信息修改)
INPUT_VIDEO="~/thesis_videos/your_video_file_1920x1080_30.yuv"
RESOLUTION="1920x1080"
FPS="30"
QP_VALUE="27" # 例如，使用QP=27
OUTPUT_VIDEO="output_intra_qp${QP_VALUE}.hevc"

# 执行编码的完整命令
# --keyint 1 : 设置为全帧内编码
# --qp ${QP_VALUE} : 设置为固定QP编码
# -o : 指定输出文件名

./x265_git/source/x265 \
--input ${INPUT_VIDEO} \
--input-res ${RESOLUTION} \
--fps ${FPS} \
--keyint 1 \
--qp ${QP_VALUE} \
-o ${OUTPUT_VIDEO}
```
