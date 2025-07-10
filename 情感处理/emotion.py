from snownlp import SnowNLP
import json

def analyze_sentiment(text):
    # 创建 SnowNLP 对象
    s = SnowNLP(text)
    # 获取情感分析得分，范围在 0 到 1 之间，越接近 1 表示越积极，越接近 0 表示越消极
    sentiment_score = s.sentiments
    # if sentiment_score > 0.5:
    #     return '积极', sentiment_score
    # elif 0.4 < sentiment_score <= 0.5:
    #     return '中性', sentiment_score
    # else:
    #     return '消极', sentiment_score
    return sentiment_score

# 输入文件路径
input_path = "新数据集\环保马克杯.txt"  # 假设这是包含原始数据的文件
# 输出文件路径
output_path = "新数据集\环保马克杯.txt"

# 读取原始数据
with open(input_path, "r", encoding='utf-8') as f:
    data = json.loads(f.read())

# 对每条评论进行情感分析并添加得分
for item in data:
    for comment in item["comment"]:
        score = analyze_sentiment(comment["评论"])
        comment["Snownlp得分"] = round(score, 5)  # 保留4位小数
        # comment["情感倾向"] = sense  # 也可以添加情感倾向标签

# 将结果写入新文件
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)  # 使用indent美化输出格式

print("情感分析完成，结果已保存到", output_path)