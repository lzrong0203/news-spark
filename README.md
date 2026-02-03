# News Spark

新聞與訊息分析工具，用於產生有趣短片素材。

## 專案目標

透過 AI 分析新聞與資訊來源，萃取有價值的內容，作為產生病毒式短影片的素材。

## 技術架構

- **Backend**: Python (分析 Agent)
- **Frontend**: Streamlit (快速建立互動式介面)
- **AI/ML**: 待定

## 目錄結構

```
news-spark/
├── src/
│   ├── agents/        # 分析 Agent
│   ├── scrapers/      # 資料抓取
│   └── utils/         # 工具函式
├── app/               # Streamlit 應用
├── data/              # 資料存放
├── tests/             # 測試
└── docs/              # 文件
```

## 安裝

```bash
# 建立虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安裝依賴
pip install -r requirements.txt
```

## 執行

```bash
streamlit run app/main.py
```

## License

GPL-3.0
