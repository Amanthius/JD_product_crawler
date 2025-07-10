import json
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image as Image



# 将数据保存到文件
file_path = "新数据集/环保背包_分词.json"


# 读取文件内容
with open(file_path, 'r', encoding='utf-8') as f:
    read_content = f.read()

# 将字符串转为字典
data = json.loads(read_content)

# 定义用于存储评价频次的字典comment_dict
comment_dict = {}
cloud = []

# 遍历数据
for item in data:
    for comment in item["comment"]:
        cloud.extend(comment["分词"])

# 统计词频
for key in cloud:
    if len(key) <= 1:
        continue
    else:
        if key not in comment_dict:
            comment_dict[key] = 1
        else:
            comment_dict[key] += 1

# 过滤低频词
h = []
for i in comment_dict.keys():
    if comment_dict[i] < 20:
        h.append(i)
for j in h:
    del comment_dict[j]

# 排序
sorted_word_freq = sorted(comment_dict.items(), key=lambda item: item[1], reverse=True)
print(sorted_word_freq)
stopwords = ["不错"]
# 去除停用词
for i in stopwords:
    if i in comment_dict:
        del comment_dict[i]

# 读取遮罩图片
mask_img = np.array(Image.open("背包.png"))

# 创建词云对象
wordcloud = WordCloud(
    font_path='simsun.ttc',  # 设置字体
    max_words=10000,  # 词云显示的最大词数
    mask=mask_img,  # 设置背景图片
    stopwords=stopwords,
    background_color='white'  # 背景颜色
)
wordcloud.generate_from_frequencies(comment_dict)

# 显示词云
plt.imshow(wordcloud)
plt.axis("off")
plt.show()