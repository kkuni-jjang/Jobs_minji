from pymongo import MongoClient
import os

# 1. MongoDB 접속 URI
# 예: mongodb://username:password@host:port/database
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://admin:yourpassword@localhost:27017/?authSource=admin")

# 2. 클라이언트 연결
client = MongoClient(MONGO_URI)

# 3. 데이터베이스 및 컬렉션 선택
db = client["job_postings"]
collection = db["wanted_jobs"]

# 4. 데이터 불러오기
docs = list(collection.find().limit(10))  # 예시: 10개 불러오기

# 5. DataFrame으로 변환 (선택)
import pandas as pd
df = pd.DataFrame(docs)

df.head()


2025-07-16T01:09:53
