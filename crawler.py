from DrissionPage import Chromium
from DrissionPage.common import Settings
import time
import random
import json
from DrissionPage import Chromium, ChromiumOptions
import re
Settings.set_language('zh_cn')

Settings.raise_when_ele_not_found = False

def get_sku_list(page):
    """
    从搜索页面获取商品的 SKU 列表
    :param page: ChromiumPage 实例
    :return: SKU 列表
    """
    sku_list = []
    count = 1
    while count <= 11:
        # 等待页面加载
        time.sleep(random.uniform(1, 2))
        btn = page("下一页", timeout=2)
        glwarp = page.ele(".gl-warp clearfix")
        links = glwarp.eles('tag:li')

        for link in links:
            sku = link.attr('data-sku')
            if sku:
                sku_list.append(sku)
        if btn:
            try:
                btn.click(by_js=True)
            except Exception as e:
                print(f"点击下一页出错: {e}")
            page.wait.load_start()
            count += 1
            # 点击后等待一段时间
            time.sleep(random.uniform(1, 2))
        else:
            break
    return sku_list

def extract_percentage(text):
    # 使用正则表达式查找文本中的百分比
    match = re.search(r'\d+%', text)
    if match:
        return match.group()
    return ""

def setup_page(page,sku):
    """
    对页面进行初始化设置，包括禁用元素未找到时的报错，
    创建 ChromiumPage 实例并打开指定网页，启动监听。
    """
    # 设置元素未找到时不报错
    Settings.raise_when_ele_not_found = False

    # 打开商品页面
    page.get(f"https://item.jd.com/{sku}.html")
    #获取商品信息
    info=page.ele(".sku-name").text
    price=page.ele(".p-price").text
    haop=page.ele(".applause-rate").text
    haopp=extract_percentage(haop)
    # 启动监听客户端动作
    page.listen.start('client.action')
    return page,info,price,haopp


def click_all_reviews(page):
    """
    查找“全部评价”按钮并点击，触发页面加载。
    """
    # 查找“全部评价”按钮
    time.sleep(0.5)
    btn = page("全部评价", timeout=2)
    if btn:
        # 通过 JavaScript 点击按钮
        btn.click(by_js=True)
        # 等待页面加载开始



def perform_actions_and_get_responses(page):
    """
    执行页面操作，如点击、滚动等，
    并等待监听获取一定数量的响应。
    """
    # 检查元素是否存在

    width = page.run_js('return document.documentElement.scrollWidth')
    height = page.run_js('return document.documentElement.scrollHeight')

# 计算中心点坐标
    center_x = width // 2
    center_y = height // 2

# 将鼠标移动到页面中央
    page.actions.move_to((center_x, center_y))
    page.actions.m_click()
    # 模拟鼠标向下滚动
    page.actions.down(400)
    # 等待获取 15 个响应
    responses = page.listen.wait(count=30,timeout=12,fit_count=False)
    # 模拟鼠标点击
    page.actions.m_click()
    if not isinstance(responses, (list, tuple)):
        return []
    
    return responses


def extract_comments(responses):
    """
    从获取的响应中提取评论信息并打印。
    """
    comment_list=[]
    
    for response in responses:
        try:
            # 获取响应体的 JSON 数据
            json_data = response.response.body
            if "result" in json_data and json_data["result"]:
                result = json_data["result"]
                floors = result["floors"]
                datas = floors[2]['data']
                for data in datas:
                    if "commentInfo" in data and data['commentInfo']:
                        comment_dict={}
                        comment_info = data['commentInfo']
                        comment_data = comment_info["commentData"]
                        comment_ID=comment_info["commentId"]
                        comment_Date=comment_info["commentDate"]
                        comment_dict["用户ID"]=comment_ID
                        comment_dict["评论"]=comment_data
                        comment_dict["评论日期"]=comment_Date
                        comment_list.append(comment_dict)
        except (KeyError, IndexError):
            continue
    return comment_list

def goods(page,sku,list):
    """
    主函数，按顺序调用其他函数完成整个流程。
    """
    dict={}
    page,info,price,haopp = setup_page(page,sku)
    click_all_reviews(page)
    responses = perform_actions_and_get_responses(page)
    comment_list=extract_comments(responses)
    
    dict['url']=f"https://item.jd.com/{sku}.html"
    dict['商品信息']=info
    dict ["价格"]=price
    dict ["好评率"]=haopp
    dict['comment']=comment_list
    
    list.append(dict)

        
def main():
    """
    主函数，程序入口
    """
    # 创建配置对象（默认从 ini 文件中读取配置）
    co = ChromiumOptions()

# 设置不加载图片、静音
    USER_AGENTS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36", 
    co.set_user_agent(USER_AGENTS)
    co.no_imgs(True).mute(False)
    browser = Chromium(4337)
    
    page = browser.latest_tab 
    page.get("https://search.jd.com/Search?keyword=%E7%8E%AF%E4%BF%9D%E8%8A%82%E7%BA%A6%E9%A9%AC%E5%85%8B%E6%9D%AF&psort=4&stock=1&psort=4&pvid=bb31b88cd49a4798a61cb3e9c7924bfc&click=1")
    page.set.NoneElement_value('￥')
    sku_list = get_sku_list(page)
    #爬取前50个商品
    sku_list = sku_list[:50]
    print(sku_list)
    list=[]
    for i, sku in enumerate(sku_list):
        goods(page, sku, list)
        if i % 5 == 0:  # 每爬5个休息一次
            time.sleep(random.uniform(5, 10))
            

    with open("环保马克杯.txt","a",encoding="utf-8") as f:
                json.dump(list, f, ensure_ascii=False, indent=4)
                f.close()
main()

