# 导入 requests 库，用于发送 HTTP 请求
import requests
# 导入 BeautifulSoup 类，用于解析 HTML 内容
from bs4 import BeautifulSoup
import os   
from dotenv import load_dotenv
import json
import time  # 新增：用于添加请求间隔，反爬友好
from requests.exceptions import RequestException  # 新增：捕获请求相关异常

# 加载环境变量文件
load_dotenv()

# 定义小说下载文件的保存路径
# 修改成自己的路径
download_file = os.getenv('bookdownloadpath')

def create_directory(path):
    '''创建目录并处理可能的异常'''
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            print(f"目录 {path} 创建成功")
        return True
    except OSError as e:
        print(f"创建目录失败: {e}")
        return False
    

# 定义请求头，模拟浏览器访问，包含 User-Agent 和 Cookie 信息
header = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Cookie": "RK=l8ddF5TuY5; ptcz=158987540fb4fd9be6cbef5d710bb8e0232af153fff8cc70afb12caad5207d13; logTrackKey=b08d0b486032425ea89cc4045406be5e; secToken=c409854e0565244cd9ab87d5a8deb6bd; fuid=6239ac79c37e4a6db88b54c9cb2395f2; ETCI=1a6e6dcb02664d1b921851d9050cc9ed; msecToken=8f1f33cf9e7f38b76a0ffe5eb6138242; g_f=4000001; Hm_lvt_6d2e509fb289d49684b88034406cc747=1753698523; HMACCOUNT=10F6FA9B2F99239B; ldhbRecord=-1; Hm_lpvt_6d2e509fb289d49684b88034406cc747=1753754269"
}

# 确保下载目录存在
if not create_directory(download_file):
    print("创建目录失败，程序退出")
    exit(1)

# 统计变量，用于进度展示
total_books = 0
success_books = 0
failed_books = 0

# 遍历排行榜页面（1~100页）
for page in range(1, 101):  # 1~100是从网站看到的，记得自己改
    print(f"\n===== 开始处理第 {page} 页 =====")
    
    # 发送 HTTP 请求，获取小说排行榜页面内容
    try:
        # 新增：添加随机间隔，避免固定频率请求
        time.sleep(1 + (page % 3) * 0.5)
        
        bigcontent = requests.get(
            f"https://book.qq.com/book-cate/0-0-0-0-0-0-0-{page}", 
            headers=header,
            timeout=10
        )
        bigcontent.raise_for_status()  # 检查HTTP错误状态码
    except ConnectionError:
        print(f"第 {page} 页 - 网络连接失败，跳过该页")
        continue
    except TimeoutError:
        print(f"第 {page} 页 - 请求超时，跳过该页")
        continue
    except RequestException as e:
        print(f"第 {page} 页 - 获取页面失败: {str(e)}，跳过该页")
        continue

    # 解析排行榜目录，使用 lxml 解析器创建 BeautifulSoup 对象
    try:
        bigcontentsoup = BeautifulSoup(bigcontent.text, 'lxml')
        # 从解析结果中选择所有类名为 'book-large' 的 div 元素
        elements = bigcontentsoup.select("div.book-large")
        
        if not elements:
            print(f"第 {page} 页 - 未找到任何书籍元素，可能页面结构已变更")
            continue
            
        print(f"第 {page} 页 - 发现 {len(elements)} 本书籍，开始处理...")
        
    except Exception as e:
        print(f"第 {page} 页 - 解析页面失败: {str(e)}，跳过该页")
        continue

    # 遍历每个小说元素
    for element in elements:
        total_books += 1
        book_id = element.get('mulan-bid')
        
        if not book_id:
            print("跳过：未找到书籍ID")
            failed_books += 1
            continue

        try:
            # 新增：请求章节列表前添加间隔
            time.sleep(0.8)
            
            # 解析章节目录，发送请求获取指定小说的章节列表
            chapter_response = requests.get(
                f"https://ubook.reader.qq.com/api/book/chapter-list?bid={book_id}", 
                headers=header,
                timeout=10
            )
            chapter_response.raise_for_status()
            
        except RequestException as e:
            print(f"书籍ID: {book_id} - 获取章节列表失败: {str(e)}，跳过本书")
            failed_books += 1
            continue

        # 解析章节列表JSON
        try:
            chapter_data = chapter_response.json()
            
            # 验证API响应结构
            if not isinstance(chapter_data, dict) or "data" not in chapter_data:
                raise ValueError("章节列表响应结构不正确")
                
            if "chapters" not in chapter_data["data"]:
                raise ValueError("未在响应中找到章节列表")
                
            chapters = chapter_data["data"]["chapters"]
            
            if not chapters:
                print(f"书籍ID: {book_id} - 未找到任何章节，跳过本书")
                failed_books += 1
                continue
                
        except json.JSONDecodeError:
            print(f"书籍ID: {book_id} - 章节列表JSON解析失败，跳过本书")
            failed_books += 1
            continue
        except Exception as e:
            print(f"书籍ID: {book_id} - 处理章节列表失败: {str(e)}，跳过本书")
            failed_books += 1
            continue

        # 遍历章节列表中的每个章节
        booktitle = None
        chapter_count = 0
        for seq in chapters:
            # 检查必要字段是否存在
            if not all(key in seq for key in ["free", "seq", "title"]):
                print(f"章节数据不完整，跳过该章节")
                continue

            # 只下载免费内容，如果章节不是免费的，则跳过
            if not seq["free"]:
                continue

            # 获取章节序号和标题
            chapter_id = seq["seq"]
            chapter_title = seq["title"]
            

            try:
                # 新增：请求章节内容前添加间隔
                time.sleep(0.5)
                
                # 修正字符串引号问题，发送请求获取章节内容页面
                detail_response = requests.get(
                    f"https://ubook.reader.qq.com/book-read/{book_id}/{chapter_id}", 
                    headers=header,
                    timeout=10
                )
                detail_response.raise_for_status()
                
            except RequestException as e:
                print(f"书籍ID: {book_id} - 章节 {chapter_id} 获取失败: {str(e)}，跳过该章节")
                continue

            # 解析章节内容
            try:
                soup = BeautifulSoup(detail_response.text, 'lxml')
                
                # 获取书籍标题（只需要获取一次）
                if not booktitle:
                    title_tag = soup.find('h2', class_='header')
                    if title_tag:
                        booktitle = title_tag.text.strip()
                    else:
                        booktitle = f"未知书籍_{book_id}"
                        print(f"书籍ID: {book_id} - 未找到书籍标题，使用默认名称")

                # 从解析结果中选择所有类名为 'chapter-content' 的 div 下的 p 元素
                content_elements = soup.select("div.chapter-content p")
                
                if not content_elements:
                    print(f"书籍《{booktitle}》- 章节 {chapter_id} 未找到内容，跳过该章节 ")
                    #可能是一些番外和废话
                    continue
                    
            except Exception as e:
                print(f"书籍ID: {book_id} - 章节 {chapter_id} 解析失败: {str(e)}，跳过该章节")
                continue

            # 写入文件
            try:
                # 使用 os.path.join 处理路径拼接，更安全
                file_path = os.path.join(download_file, f"{booktitle}.txt")
                
                # 以追加模式打开文件，将章节内容写入文件
                with open(file_path, "a", encoding="utf-8") as f:
                    # 写入章节标题
                    f.write(f"{chapter_title}\n")
                    # 遍历每个段落，去除换行符后写入文件
                    for para in content_elements:
                        f.write(para.text.replace("\n", ""))
                    # 写入换行符分隔不同章节
                    f.write("\n\n")

                # 打印已下载的章节信息（取消注释）
                print(f"书籍《{booktitle}》- 已下载第 {chapter_id} 章：{chapter_title}")
                
            except Exception as e:
                print(f"书籍《{booktitle}》- 章节 {chapter_id} 写入失败: {str(e)}，跳过该章节")
                continue
            chapter_count += 1
        # 完成一本书的处理
        if booktitle:
            success_books += 1
            print(f"\n✅ 已完成《{booktitle}》的下载，共获取 {chapter_count} 个免费章节")
        else:
            failed_books += 1

# 全部处理完成后显示统计信息
print("\n" + "="*50)
print(f"爬虫任务完成！")
print(f"总处理书籍数: {total_books}")
print(f"成功下载书籍数: {success_books}")
print(f"失败书籍数: {failed_books}")
print(f"下载目录: {os.path.abspath(download_file)}")
print("="*50)
