import websocket
import pymongo
import json

# 连接到 MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["RSM"]

# 定义 WebSocket 接收消息的回调函数
def on_message(ws, message):
    try:
        # 解析收到的 JSON 格式数据
        rsm_data = json.loads(message)
        if rsm_data["type"] != 14:
            return
        if "mecEsn" not in rsm_data["data"]:
            print("RSM 数据中不存在mecEsn字段")
            return
        rsu_id = rsm_data["data"]["mecEsn"]
        # 检查是否已经存在对应的集合，如果不存在则创建
        if rsu_id not in db.list_collection_names():
            db.create_collection(rsu_id)
        # 将数据插入到相应的集合中，并创建 timestamp 字段的索引
        collection = db[rsu_id]
        collection.create_index([(str(rsm_data["data"]["rsms"][0]["participants"][0]["timestamp"]), pymongo.ASCENDING)], expireAfterSeconds=1*60, unique=True, sparse=True)
        collection.insert_one(rsm_data)
        print("数据插入成功！")
    except Exception as e:
        print(e)

# 创建 WebSocket 连接
ws = websocket.WebSocketApp("ws://36.138.2.41:9873/api/websocket/connectServer/sim-gicc",
                            on_message = on_message)

# 运行 WebSocket
ws.run_forever()