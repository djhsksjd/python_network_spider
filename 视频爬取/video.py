# 导入tabnanny模块，用于检查Python代码缩进是否符合规范
import tabnanny
# 导入time模块，用于获取当前时间戳
import time
# 从tracemalloc模块导入take_snapshot函数，不过本代码中未实际使用该函数
from tracemalloc import take_snapshot
# 导入requests模块，用于发送HTTP请求
import requests
# 导入hashlib模块，用于生成哈希值
import hashlib
# 导入os模块，用于与操作系统进行交互，如获取环境变量
import os
# 从dotenv模块导入load_dotenv函数，用于加载环境变量
from dotenv import load_dotenv
# 导入requests异常处理模块
from requests.exceptions import RequestException
# 导入colorama模块，用于在终端添加颜色支持
from colorama import init, Fore, Style

# 初始化colorama，确保颜色在终端中正确显示
init(autoreset=True)

try:
    # 加载环境变量
    load_dotenv()
except Exception as e:
    print(f"环境变量加载失败: {e}")
    exit(1)

try:
    # 从环境变量中获取视频下载路径
    download_path = os.getenv('videodownloadpath')
    if not download_path:
        raise ValueError("环境变量中未找到videodownloadpath配置")
    
    # 确保下载路径存在
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    if not os.path.isdir(download_path):
        raise NotADirectoryError(f"{download_path}不是有效的目录")
except Exception as e:
    print(f"下载路径配置错误: {e}")
    exit(1)

try:
    # 生成时间戳，减去9999可能是为了对时间戳进行调整
    _ts = str(int(time.time()*1000 - 9999))
    if len(_ts) != 13:
        raise ValueError(f"生成的时间戳格式异常: {_ts}")
except Exception as e:
    print(f"时间戳生成错误: {e}")
    exit(1)

# 以下为注释掉的代码，可用于手动输入搜索关键词和页码
# keyword = input("输入想要搜索的视频")
# page = int(input('输入想要搜索的页码'))
# testtime = "1753868346935"
# 设置搜索关键词为火车
keyword = '火车'
# 设置搜索页码为1
page = 1
# 设置每页显示的结果数量为12
limit = 12

try:
    # 构建用于生成签名的参数字符串
    strpar = f'_platform=web,_ts={_ts},_versioin=0.2.5,keyword={keyword},limit={limit},page={page},'
    
    # 对参数字符串进行MD5哈希计算，生成X-Signature
    X_Signature = hashlib.md5(strpar.encode('utf-8')).hexdigest()
    if not X_Signature:
        raise ValueError("签名生成失败")
except Exception as e:
    print(f"签名生成错误: {e}")
    exit(1)

# 设置请求头，包含X-Signature和User-Agent
header = {
    'X-Signature': str(X_Signature),
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

# 设置请求参数
params = {
    # 'keyword': keyword,
    'keyword':keyword,
    'page':str(page),
    'limit':str(limit),
    '_platform':'web',
    '_versioin':'0.2.5',
    '_ts':_ts,
}

# 示例请求URL，仅作注释参考
# Request URL https://ssv-video.agilestudio.cn/9641_5f5e78/9641_5f5e78468.ts

try:
    # 发送GET请求，搜索视频数据
    response = requests.get('https://fse-api.agilestudio.cn/api/search', headers=header, params=params, timeout=10)
    response.raise_for_status()  # 触发HTTP错误状态码异常
except RequestException as e:
    print(f"视频搜索请求失败: {e}")
    exit(1)

try:
    # 从响应结果中提取视频列表数据
    response_json = response.json()
    if 'data' not in response_json:
        raise KeyError("响应数据中缺少data字段")
    if 'list' not in response_json['data']:
        raise KeyError("响应data中缺少list字段")
    data = response_json['data']['list']
    if not isinstance(data, list):
        raise TypeError("视频列表数据不是预期的列表类型")
    print("开始下载素材")
except (json.JSONDecodeError, KeyError, TypeError) as e:
    print(f"响应数据解析错误: {e}")
    exit(1)

try:
    # 打印第一个视频的URL
    if data:
        print(data[0]['video']['url'])
except (IndexError, KeyError) as e:
    print(f"获取第一个视频URL失败: {e}")

# 以下为注释掉的代码，可用于获取并打印第一个视频的响应内容
# responsedata = requests.get(data[0]['video']['url'])
# print(responsedata.text)

# 定义一个美化后的进度条函数
def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=50, fill='█', print_end="\r"):
    """
    打印进度条，带颜色、下载速度和预计剩余时间

    :param iteration: 当前迭代次数
    :param total: 总迭代次数
    :param prefix: 进度条前缀
    :param suffix: 进度条后缀
    :param decimals: 百分比小数点位数
    :param length: 进度条长度
    :param fill: 进度条填充字符
    :param print_end: 每次打印结束的字符
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = Fore.GREEN + fill * filled_length + Style.RESET_ALL + Fore.LIGHTBLACK_EX + '-' * (length - filled_length) + Style.RESET_ALL
    # 计算下载速度和预计剩余时间
    elapsed_time = time.time() - print_progress_bar.start_time if hasattr(print_progress_bar, 'start_time') else 0
    speed = iteration / elapsed_time if elapsed_time > 0 else 0
    eta = (total - iteration) / speed if speed > 0 else 0
    print(f'\r{prefix} |{bar}| {percent}% {suffix} | Speed: {speed:.2f} ts/s | ETA: {eta:.2f} s', end=print_end)
    if iteration == total:
        print()

# 遍历视频列表
for item in data:
    try:
        # 检查视频信息是否完整
        if 'video' not in item:
            raise KeyError("视频信息中缺少video字段")
        video_info = item['video']
        for key in ['name', 'url']:
            if key not in video_info:
                raise KeyError(f"视频信息中缺少{key}字段")
        
        print("正在下载", video_info['name'])
        print ('------------------\n')
        # 获取当前视频的m3u8文件URL
        m3u8url = video_info['url']
        
        # 获取m3u8文件内容
        try:
            response = requests.get(m3u8url, timeout=10)
            response.raise_for_status()
            m3u8data = response.text
        except RequestException as e:
            print(f"获取m3u8文件失败: {e}，跳过该视频")
            continue
        
        # 将m3u8文件内容按行分割
        m3u8lines = m3u8data.split('\n')
        # 筛选出.ts文件的行
        ts_lines = [line for line in m3u8lines if '.ts' in line]
        total_ts = len(ts_lines)
        
        if total_ts == 0:
            print("未找到任何.ts片段，跳过该视频")
            continue
        
        # 对视频名称进行 sanitization，移除Windows不允许的字符
        invalid_chars = '\/:*?"<>|'
        sanitized_name = ''.join([c for c in video_info['name'] if c not in invalid_chars])
        
        # 记录下载开始时间
        print_progress_bar.start_time = time.time()
        
        # 遍历.ts文件行
        for index, line in enumerate(ts_lines, start=1):
            try:
                # 构建.ts文件的完整URL
                ts_url = m3u8url[:m3u8url.rfind('/') + 1] + line
                
                # 获取.ts文件内容
                ts_response = requests.get(ts_url, timeout=10)
                ts_response.raise_for_status()
                
                # 构建完整保存路径
                save_path = os.path.join(download_path, f"{sanitized_name}.mp4")
                
                # 将.ts文件内容写入到对应的.mp4文件中
                with open(save_path, 'ab') as f:
                    f.write(ts_response.content)
                
                # 更新并打印进度条
                print_progress_bar(index, total_ts, prefix='下载进度:', suffix='完成', length=50)
                print("下载完成", line)
                print ('------------------\n')
            except RequestException as e:
                print(f"下载.ts片段 {line} 失败: {e}，继续下一个片段")
            except IOError as e:
                print(f"写入文件失败: {e}，跳过该片段")
        
        print("下载完成")
        print ('------------------\n')
    except KeyError as e:
        print(f"视频信息解析错误: {e}，跳过该视频")
    except Exception as e:
        print(f"处理视频时发生错误: {e}，跳过该视频")

print("所有视频处理完毕")