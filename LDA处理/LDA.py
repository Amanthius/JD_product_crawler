import json
import jieba
import numpy as np
import os
from gensim import corpora, models
from gensim.models.coherencemodel import CoherenceModel
from snownlp import SnowNLP

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

# 执行LDA分析并评估不同主题数
def run_lda_with_evaluation(docs, min_topics=3, max_topics=5):
    if not docs:
        print("无有效数据可分析")
        return None
    
    dictionary = corpora.Dictionary(docs)
    corpus = [dictionary.doc2bow(doc) for doc in docs]
    
    best_model = None
    best_coherence = -1
    best_num_topics = 0
    
    # 遍历不同主题数
    for num_topics in range(min_topics, max_topics + 1):
        model = models.LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=num_topics,
            passes=15,
            alpha='auto',
            random_state=42
        )
        
        # 计算一致性分数
        coherence = CoherenceModel(
            model=model,
            texts=docs,
            dictionary=dictionary,
            coherence='c_v'
        ).get_coherence()
        
        print(f"主题数: {num_topics}, 一致性分数: {coherence:.3f}")
        
        if coherence > best_coherence:
            best_coherence = coherence
            best_model = model
            best_num_topics = num_topics
    
    print("\n最优模型结果:")
    print(f"最优主题数: {best_num_topics}")
    print(f"最优一致性分数: {best_coherence:.3f}")
    print("\n主题关键词分布:")
    
    for idx in range(best_num_topics):
        topic = best_model.show_topic(idx, topn=10)
        print(f"主题{idx+1}: {', '.join([w[0] for w in topic])}")
    
    return best_model, dictionary

# 为每条评论分配主题
def assign_topics(products, model, dictionary):
    for product in products:
        for comment in product['comment']:
            text = comment['评论']
            processed_text = deep_preprocess([text], load_stopwords())
            if processed_text:
                bow = dictionary.doc2bow(processed_text[0])
                topics = model.get_document_topics(bow)
                dominant_topic = max(topics, key=lambda x: x[1])[0]
                comment['主题'] = dominant_topic + 1  # 主题编号从 1 开始
    return products

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
    
    print(f"总有效评论数: {len(processed_comments)}")
    
    # 执行LDA分析
    print("\n开始LDA主题分析...")
    print("评估不同主题数效果:")
    lda_model, dictionary = run_lda_with_evaluation(processed_comments, min_topics=3, max_topics=7)#主题数调整
    
    # 为每条评论分配主题
    updated_products = assign_topics(products, lda_model, dictionary)
    
    # 保存更新后的 JSON 文件
    output_file_path = os.path.join('新数据集', '环保马克杯.json')
    with open(output_file_path, 'w', encoding='utf-8') as f:
        json.dump(updated_products, f, ensure_ascii=False, indent=4)
    
    print(f"\n已将主题信息添加到评论中，并保存为 {output_file_path}")

if __name__ == "__main__":
    full_analysis()