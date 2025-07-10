import json
import csv
import re
from typing import List, Dict, Any

def clean_comment(comment: str) -> str:
    """清洗评论内容：将空行替换为逗号"""
    cleaned = comment.strip()
    return re.sub(r'\n+', ', ', cleaned)

def process_document_to_csv(document_content: str, csv_filename: str) -> None:
    """将文档内容转换为CSV文件，增加字段存在性检查"""
    cleaned_content = document_content.replace('<! [CDATA [', '').replace(']]>', '').strip()
    data = json.loads(cleaned_content)
    
    rows: List[Dict[str, str]] = []
    for item in data:
        product_info = item["商品信息"]
        price = item["价格"]
        haopp = item["好评率"]
        
        for comment_data in item["comment"]:
            # 处理评论中的空行
            processed_comment = clean_comment(comment_data["评论"])
            
            # 检查主题字段是否存在，不存在则设为默认值
            theme = comment_data.get("主题", "未标注")  # 可根据需求修改默认值
            rows.append({
                "商品信息": product_info,
                "价格": price,
                "好评率": haopp,
                "用户ID": comment_data["用户ID"],
                "评论": processed_comment,
                "评论时间": comment_data["评论日期"],
                "主题(LDA)": str(theme),
                "SnowNLP得分(因变量)":comment_data["Snownlp得分"],
                "分词":comment_data["分词"]
            })
    
    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["商品信息", "价格", "好评率", "用户ID", "评论", "评论时间", "主题(LDA)","SnowNLP得分(因变量)","分词"])
        writer.writeheader()
        writer.writerows(rows)

# 读取文档内容
with open('新数据集\环保马克杯_分词.txt', 'r', encoding='utf-8') as f:
    document_content = f.read()

csv_output_filename = '新数据集\环保马克杯_分词.csv'
process_document_to_csv(document_content, csv_output_filename)

print(f"转换完成！结果已保存至 {csv_output_filename}")