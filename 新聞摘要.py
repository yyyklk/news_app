#%%
import json
import os
import streamlit as st
from snownlp import SnowNLP
import jieba.analyse
import datetime

#%%
st.set_page_config(

    layout="wide"

)
#%%
def normalize_text(text):
    """統一台/臺字元"""
    return text.replace('臺', '台')

#%%
st.title('新聞資料庫')
st.markdown("----")
c1, c2 = st.columns(2)
with c1:
    date_filter_s = st.date_input("篩選新聞日期（開始時間）", value=datetime.date(2025, 6, 28), min_value=datetime.date(2025, 6, 28))
with c2:
    date_filter_e = st.date_input("篩選新聞日期（結束時間）", value=datetime.date.today(), min_value=datetime.date(2025, 6, 28))
st.markdown("----")

# 動態新增關鍵詞輸入框
if 'keyword_count' not in st.session_state:
    st.session_state.keyword_count = 0

col1, col2 = st.columns(2)
with col1:
    st.write("**新聞關鍵詞搜尋:**")
    if st.button("新增關鍵詞"):
        st.session_state.keyword_count += 1

with col2:
    st.write("**減少關鍵詞搜尋:**")
    if st.button("減少關鍵詞"):
        if st.session_state.keyword_count > 0:
            st.session_state.keyword_count -= 1

# 收集所有關鍵詞
keywords = []
for i in range(st.session_state.keyword_count):
    keyword = st.text_input(f'關鍵詞 {i+1}', key=f"news_keyword{i+1}")
    if keyword.strip():  # 只收集非空的關鍵詞
        keywords.append(keyword.strip())

# 顯示搜尋狀態
if keywords:
    st.info(f"將搜尋包含以下關鍵詞的新聞: {', '.join(keywords)}")
else:
    st.info("未輸入關鍵詞，將顯示所有新聞")

st.markdown("----")


######################################################################################
#%%
def keyword_summary(text, num_sentences=3):
    """基於關鍵詞的摘要"""
    keywords = jieba.analyse.extract_tags(text, topK=10)
    sentences = text.split('。')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    sentence_scores = []
    for sentence in sentences:
        score = sum(1 for kw in keywords if kw in sentence)
        sentence_scores.append((sentence, score))
    
    top_sentences = sorted(sentence_scores, key=lambda x: x[1], reverse=True)
    return [s[0] for s in top_sentences[:num_sentences] if s[0]]



#%%
json_folder = os.path.join(os.path.dirname(__file__), 'data')  # 相對於程式碼檔案的 data 資料夾
news_path = os.path.join(json_folder, 'combined_news.json')
# 確保資料夾存在
if not os.path.exists(json_folder):
    st.error(f"找不到資料夾: {json_folder}")
    st.stop()

# 確保 JSON 檔案存在
if not os.path.exists(news_path):
    st.error(f"找不到新聞檔案: {news_path}")
    st.stop()
    
with open(news_path, 'r', encoding='utf-8') as f:
    news_list = json.load(f)

# 篩選邏輯
filtered_news = []

for news in news_list:
    # 1. 日期篩選
    news_date = datetime.datetime.strptime(news['日期'], '%Y-%m-%d').date()
    if not (date_filter_s <= news_date <= date_filter_e):
        continue
    
    # 2. 關鍵詞篩選
    if keywords:
        # 將標題和內容統一字元
        text_to_search = normalize_text(news['標題'] + news['內容'])
        # 將關鍵詞也統一字元
        normalized_keywords = [normalize_text(keyword) for keyword in keywords]
        
        if not all(keyword in text_to_search for keyword in normalized_keywords):
            continue
    
    # 通過篩選的新聞加入列表
    filtered_news.append(news)

# 顯示篩選結果
st.write(f"**篩選結果: 共 {len(filtered_news)} 則新聞**")
st.markdown("----")

# 新增執行摘要的按鈕
if st.button("🔍 開始進行新聞摘要", type="primary"):
    if filtered_news:
        # 顯示進度條
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        #%%
        # 對篩選後的新聞進行摘要
        for idx, news in enumerate(filtered_news):
            # 更新進度
            progress = (idx + 1) / len(filtered_news)
            progress_bar.progress(progress)
            status_text.text(f'正在處理第 {idx + 1}/{len(filtered_news)} 則新聞...')
            
            text = news['內容']
            
            # 方法1: SnowNLP TextRank
            s = SnowNLP(text)
            textrank_summary = list(s.summary(3))
            
            # 方法2: 關鍵詞摘要
            keyword_sum = keyword_summary(text, 3)
            
            st.subheader(f"{news['標題']}", divider='rainbow')
            st.write(f"日期: {news['日期']}")
            
            with st.expander("查看完整新聞內容"):
                st.code(news['內容'])

            st.write("**TextRank 摘要:**")
            for i, sentence in enumerate(textrank_summary, 1):
                st.write(f"{i}. {sentence}")
            
            st.write("**關鍵詞摘要:**")
            for i, sentence in enumerate(keyword_sum, 1):
                st.write(f"{i}. {sentence}")
            
            # 保存兩種摘要
            news['TextRank摘要'] = textrank_summary
            news['關鍵詞摘要'] = keyword_sum
            
            if '內容' in news:
                del news['內容']
        
        # 清除進度條
        progress_bar.empty()
        status_text.empty()
    else:
        st.warning("沒有符合篩選條件的新聞，無法進行摘要")
else:
    if filtered_news:
        st.info("📋 點擊上方按鈕開始進行新聞摘要")
    else:
        st.warning("沒有符合篩選條件的新聞")