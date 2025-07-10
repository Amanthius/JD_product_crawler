import json
import jieba
import numpy as np
import os
import matplotlib.pyplot as plt
from gensim import corpora, models
from gensim.models.coherencemodel import CoherenceModel
from collections import defaultdict
from sklearn.decomposition import PCA
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 禁用jieba调试输出
jieba.setLogLevel(20)

# 加载停用词表
def load_stopwords(stopwords_path='新LDA处理/stopwords.txt'):
    with open(stopwords_path, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

# 数据预处理强化版
def deep_preprocess(comments, stopwords):
    processed = []
    for comment in comments:
        if not isinstance(comment, str):
            comment = str(comment)
        
        words = jieba.lcut(comment.strip())
        filtered = [
            word.lower()
            for word in words
            if len(word) > 1
            and word.isalnum()
            and not word.isdigit()
            and word not in stopwords
        ]
        if filtered:
            processed.append(filtered)
    return processed

# 可视化主题权重
def visualize_topics(topic_data, word_freq, label="主题分析", output_dir='visualizations'):
    if not topic_data:
        print(f"\n【{label}】无有效主题数据可展示")
        return
    
    # 检查坐标数据是否有效
    for t in topic_data:
        if len(t['coords']) < 2:
            t['coords'] = [0, 0]
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 调整圆圈大小
    x = [t['coords'][0] for t in topic_data]
    y = [t['coords'][1] for t in topic_data]
    sizes = [t['avg_prob'] * 48000 for t in topic_data]
    topics = [f"主题{i+1}" for i in range(len(topic_data))]
    
    # 收集所有主题的单词数据
    all_words_data = []
    for t in topic_data:
        words = t['words'][:10]  # 只取前10个词
        doc_freqs = [w['doc_freq'] for w in words]
        topic_weights = [w['topic_weight'] for w in words]
        all_words_data.append((words, doc_freqs, topic_weights))
    
    # 创建主图
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.6, 0.4],
        specs=[[{"type": "scatter"}, {"type": "bar"}]],
        horizontal_spacing=0.05
    )
    
    # 散点图
    scatter = go.Scatter(
        x=x,
        y=y,
        mode='markers+text',
        marker=dict(
            size=sizes,
            sizemode='area',
            # 调整圆圈大小
            sizeref=2.*max(sizes)/(120.**2),
            color='#1f77b4',
            opacity=0.7,
            line=dict(width=1, color='DarkSlateGrey')
        ),
        text=topics,
        textposition='middle center',
        customdata=all_words_data,
        hoverinfo='none'
    )
    
    fig.add_trace(scatter, row=1, col=1)
    
    # 为每个主题创建关键词条形图
    buttons = []
    for idx in range(len(topic_data)):
        words, doc_freqs, topic_weights = all_words_data[idx]
        y_labels = [w['word'] for w in words]
        
        # 添加文档频率条形图
        fig.add_trace(go.Bar(
            x=doc_freqs,
            y=y_labels,
            name='文档频率',
            marker_color='blue',
            orientation='h',
            visible=(idx == 0)  # 默认只显示第一个主题
        ), row=1, col=2)
        
        # 添加主题权重条形图
        fig.add_trace(go.Bar(
            x=topic_weights,
            y=y_labels,
            name='主题权重',
            marker_color='red',
            orientation='h',
            visible=(idx == 0)  # 默认只显示第一个主题
        ), row=1, col=2)
        
        # 创建按钮
        button = dict(
            label=f'主题 {idx+1}',
            method='update',
            args=[{'visible': [True] + [False]*(len(topic_data)*2)}]
        )
        button['args'][0]['visible'][1 + idx*2] = True  # 文档频率
        button['args'][0]['visible'][2 + idx*2] = True  # 主题权重
        buttons.append(button)
    
    # 添加下拉菜单
    fig.update_layout(
        updatemenus=[{
            'buttons': buttons,
            'direction': 'down',
            'showactive': True,
            'x': 0.5,
            'y': 1.15,
            'xanchor': 'center',
            'yanchor': 'top'
        }],
        title=f"{label}主题分布与关键词分析",
        height=600,
        margin=dict(l=20, r=20, t=60, b=20),
        template='plotly_white'
    )
    
    # 生成HTML文件
    html_path = os.path.join(output_dir, f"{label}_topic_analysis.html")
    pyo.plot(fig, filename=html_path, auto_open=False)
    print(f"已生成可视化文件：{html_path}")
    
    # 为每个主题单独生成关键词图像
    for idx, (words, doc_freqs, topic_weights) in enumerate(all_words_data):
        fig_single = make_subplots(rows=1, cols=1)
        
        # 添加文档频率条形图
        fig_single.add_trace(go.Bar(
            x=doc_freqs,
            y=[w['word'] for w in words],
            name='文档频率',
            marker_color='blue',
            orientation='h'
        ))
        
        # 添加主题权重条形图
        fig_single.add_trace(go.Bar(
            x=topic_weights,
            y=[w['word'] for w in words],
            name='主题权重',
            marker_color='red',
            orientation='h'
        ))
        
        fig_single.update_layout(
            title=f"主题{idx+1}关键词分析",
            height=600,
            margin=dict(l=20, r=20, t=60, b=20),
            template='plotly_white',
            barmode='group'
        )
        
        # # 生成单独的HTML文件
        # single_html_path = os.path.join(output_dir, f"{label}topic_{idx+1}_keywords.html")
        # pyo.plot(fig_single, filename=single_html_path, auto_open=False)
        # print(f"已生成主题{idx+1}关键词可视化文件：{single_html_path}")

# LDA分析函数
def run_lda(docs, num_topics=5, label="主题分析"):
    if not docs or num_topics <= 0:
        print(f"\n【{label}】无有效数据可分析或主题数为0")
        return None, [], {}
    
    # 创建词典和语料
    dictionary = corpora.Dictionary(docs)
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    
    # 训练LDA模型
    model = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        passes=15,
        alpha='auto',
        random_state=42
    )
    
    # 获取文档主题分布
    doc_topics = [model.get_document_topics(doc) for doc in corpus]
    topic_prob_matrix = np.zeros((len(doc_topics), num_topics))
    for i, topics in enumerate(doc_topics):
        for topic_id, prob in topics:
            topic_prob_matrix[i, topic_id] = prob
    topic_avg_probs = topic_prob_matrix.mean(axis=0)
    
    # 降维处理
    topic_word_dist = model.get_topics()
    coords = np.zeros((num_topics, 2))
    
    if num_topics > 1:
        try:
            pca = PCA(n_components=min(2, num_topics))
            coords = pca.fit_transform(topic_word_dist)
            if coords.shape[1] == 1:
                coords = np.hstack([coords, np.zeros((num_topics, 1))])
        except Exception as e:
            print(f"警告：PCA降维失败，使用默认坐标: {str(e)}")
            coords = np.random.rand(num_topics, 2)
    
    # 统计词频
    word_freq = defaultdict(int)
    for doc in docs:
        for word in doc:
            word_freq[word] += 1
    total_words = sum(word_freq.values())
    word_freq = {k: v/total_words for k, v in word_freq.items()}
    
    # 收集主题数据
    topic_data = []
    for topic_id in range(num_topics):
        top_words = model.show_topic(topic_id, topn=30)
        word_data = []
        for word, weight in top_words:
            word_data.append({
                'word': word,
                'doc_freq': word_freq.get(word, 0),
                'topic_weight': weight
            })
        topic_data.append({
            'coords': coords[topic_id],
            'avg_prob': topic_avg_probs[topic_id],
            'words': word_data
        })
    
    # 计算一致性分数
    coherence = CoherenceModel(
        model=model,
        texts=docs,
        dictionary=dictionary,
        coherence='c_v'
    ).get_coherence()
    
    print(f"\n【{label}结果】")
    print(f"主题数：{num_topics}")
    print(f"一致性分数：{coherence:.3f}")
    print("主题关键词分布：")
    for idx in range(num_topics):
        topic = model.show_topic(idx, topn=10)
        print(f"主题{idx+1}: {', '.join([w[0] for w in topic])}")
    
    return model, topic_data, word_freq

# 完整分析流程
def full_analysis():
    # 数据加载
    file_path = os.path.join('新数据集', '环保马克杯.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    # 加载停用词
    stopwords = load_stopwords()
    
    # 合并并预处理评论
    raw_comments = [c['评论'] for p in products for c in p['comment']]
    processed_comments = deep_preprocess(raw_comments, stopwords)
    
    print(f"总有效评论数：{len(processed_comments)}")
    
    # 执行LDA分析（固定主题数）
    model, topic_data, word_freq = run_lda(
        processed_comments, 
        num_topics=5,  # 可以调整主题数
        label="商品评论"
    )
    
    # 可视化结果
    if topic_data:
        visualize_topics(topic_data, word_freq, label="")

if __name__ == "__main__":
    full_analysis()