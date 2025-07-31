import requests  # 导入 requests 库，用于发送 HTTP 请求
import os  # 导入 os 模块，用于文件路径操作
from dotenv import load_dotenv  # 导入 load_dotenv 函数，用于加载环境变量
import time  # 导入时间模块，用于请求间隔控制

def main():
    """
    主函数：实现图片搜索和下载的完整流程
    包括环境变量加载、用户输入处理、API请求和图片下载
    """
    # 加载环境变量，从 .env 文件中读取配置
    # 确保 .env 文件中包含 imagedownloadpath 配置项
    load_dotenv()
    
    # 从环境变量获取图片下载路径
    download_path = os.getenv('imagedownloadpath')
    
    # 验证下载路径是否有效
    if not validate_download_path(download_path):
        print("程序无法继续运行，退出。")
        return
    
    # 获取并验证用户输入
    user_input = get_user_input()
    if not user_input:
        print("用户输入无效，程序退出。")
        return
    
    query, total_pages, per_page = user_input
    print(f"开始下载---共{total_pages}页,每页{per_page}张图片")
    
    # 循环下载每一页的图片
    for current_page in range(1, total_pages + 1):
        try:
            # 发送请求获取图片列表
            photos_data = fetch_photos(query, current_page, per_page)
            
            if not photos_data:
                print(f"第 {current_page} 页没有找到图片，跳过该页。")
                continue
            
            # 下载当前页的所有图片
            download_count = download_photos(photos_data, download_path, current_page)
            print(f"第 {current_page} 页下载完成，成功下载 {download_count}/{len(photos_data)} 张图片")
            print("-" * 50)
            
            # 避免请求过于频繁，添加适当延迟
            if current_page < total_pages:
                time.sleep(1)
                
        except Exception as e:
            print(f"处理第 {current_page} 页时发生错误: {str(e)}")
            print("继续处理下一页...")
            print("-" * 50)
    
    print(f"所有下载任务已完成")

def validate_download_path(path):
    """
    验证下载路径是否有效
    
    参数:
        path: 待验证的文件路径
        
    返回:
        bool: 路径有效返回True，否则返回False
    """
    if not path:
        print("错误：未在环境变量中找到 imagedownloadpath 配置")
        return False
        
    # 检查路径是否存在，不存在则尝试创建
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            print(f"已创建下载目录: {path}")
        except OSError as e:
            print(f"错误：无法创建下载目录 {path}，原因: {str(e)}")
            return False
            
    # 检查路径是否可写
    if not os.access(path, os.W_OK):
        print(f"错误：下载目录 {path} 不可写")
        return False
        
    return True

def get_user_input():
    """
    获取并验证用户输入的搜索关键词、页数和每页数量
    
    返回:
        tuple: 包含(query, total_pages, per_page)的元组，无效则返回None
    """
    try:
        # 获取搜索关键词
        query = input("请输入要搜索的图片关键词：").strip()
        if not query:
            print("错误：搜索关键词不能为空")
            return None
            
        # 获取下载页数
        total_pages = int(input("请输入要下载的页数：").strip())
        if total_pages <= 0:
            print("错误：下载页数必须是正整数")
            return None
            
        # 获取每页数量
        per_page = int(input("请输入每页要下载的图片数量：").strip())
        if per_page <= 0 or per_page > 80:  # 通常API有最大限制
            print("错误：每页数量必须是1-80之间的整数")
            return None
            
        return (query, total_pages, per_page)
        
    except ValueError:
        print("错误：页数和每页数量必须是整数")
        return None
    except Exception as e:
        print(f"获取用户输入时发生错误: {str(e)}")
        return None

def fetch_photos(query, page, per_page):
    """
    调用API获取图片列表数据
    
    参数:
        query: 搜索关键词
        page: 页码
        per_page: 每页数量
        
    返回:
        list: 图片数据列表，获取失败返回None
    """
    # 定义请求头，包含API密钥
    headers = {
        "secret-key": "H2jk9uKnhRmL6WPwh89zBezWvr",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # 定义请求参数
    params = {
        "query": query,          # 搜索关键词
        "page": page,            # 当前页码
        "per_page": per_page,    # 每页图片数量
        "orientation": "all",    # 图片方向，全部
        "size": "all",           # 图片尺寸，全部
        "color": "all",          # 图片颜色，全部
        "sort": "popular"        # 按热门排序
    }
    
    # API请求地址
    url = 'https://www.pexels.com/zh-cn/api/v3/search/photos'
    
    try:
        # 发送GET请求，设置超时时间为10秒
        response = requests.get(
            url, 
            headers=headers, 
            params=params,
            timeout=10
        )
        
        # 检查响应状态码，200表示成功
        response.raise_for_status()
        
        # 解析JSON响应
        data = response.json()
        
        # 返回图片数据列表
        return data.get("data", [])
        
    except requests.exceptions.HTTPError as e:
        print(f"API请求失败: {str(e)}")
        if response.status_code == 403:
            print("可能是API密钥无效或已过期")
        elif response.status_code == 404:
            print("请求的API地址不存在")
    except requests.exceptions.Timeout:
        print("API请求超时")
    except requests.exceptions.ConnectionError:
        print("网络连接错误，无法连接到API服务器")
    except KeyError as e:
        print(f"API返回数据格式错误，缺少 {str(e)} 字段")
    except Exception as e:
        print(f"获取图片列表时发生错误: {str(e)}")
        
    return None

def download_photos(photos_data, download_path, current_page):
    """
    下载图片并保存到本地
    
    参数:
        photos_data: 图片数据列表
        download_path: 下载目录
        current_page: 当前页码
        
    返回:
        int: 成功下载的图片数量
    """
    success_count = 0
    
    for index, photo in enumerate(photos_data, 1):
        try:
            # 提取图片信息
            photo_id = photo.get("id", f"unknown_{current_page}_{index}")
            alt_text = photo.get("attributes", {}).get("alt", f"image_{photo_id}")
            image_url = photo.get("attributes", {}).get("image", {}).get("large")
            
            # 验证图片URL
            if not image_url:
                print(f"第 {current_page} 页 - 图片 {index} 缺少图片URL，跳过")
                continue
            
            # 处理文件名，移除特殊字符
            filename = f"{alt_text[:50].replace('/', '_').replace('\\', '_')}_{photo_id}.jpg"
            file_path = os.path.join(download_path, filename)
            
            # 下载图片
            print(f"第 {current_page} 页 - 正在下载图片 {index}/{len(photos_data)}: {filename}")
            
            # 发送请求下载图片，设置超时时间为15秒
            img_response = requests.get(image_url, timeout=15)
            img_response.raise_for_status()  # 检查HTTP错误
            
            # 保存图片到本地
            with open(file_path, "wb") as f:
                f.write(img_response.content)
            
            success_count += 1
            print(f"第 {current_page} 页 - 图片 {index} 下载成功")
            
        except requests.exceptions.HTTPError as e:
            print(f"第 {current_page} 页 - 图片 {index} 下载失败 (HTTP错误): {str(e)}")
        except requests.exceptions.Timeout:
            print(f"第 {current_page} 页 - 图片 {index} 下载失败 (超时)")
        except IOError as e:
            print(f"第 {current_page} 页 - 图片 {index} 保存失败: {str(e)}")
        except Exception as e:
            print(f"第 {current_page} 页 - 处理图片 {index} 时发生错误: {str(e)}")
        
        # 每张图片下载间隔，避免请求过于频繁
        time.sleep(0.5)
    
    return success_count

# 程序入口
if __name__ == "__main__":
    main()
