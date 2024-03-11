import redis
import os

host = os.environ['Redishostname']
port = os.environ['Redisport']

class RedisManager:
    def __init__(self, host=host, port=port, db=0):
        """初始化Redis连接"""
        self.db = redis.Redis(host=host, port=port, db=db)

    def insert_with_expiration(self, key, value, expiration=30):
        """
        插入数据并设置过期时间
        :param key: 键
        :param value: 值
        :param expiration: 过期时间（秒）
        """
        self.db.setex(key, expiration, value)

    def delete(self, key):
        """
        删除数据
        :param key: 要删除的键
        """
        self.db.delete(key)

    def get(self, key):
        """
        获取键的值
        :param key: 键
        :return: 键对应的值，如果键不存在，则返回None
        """
        value = self.db.get(key)
        if value is not None:
            return value.decode()  # 将bytes类型转换为str
        return None

# 示例使用
if __name__ == "__main__":
    # 初始化Redis管理器
    redis_manager = RedisManager(db=0)  # 连接到第一个数据库

    # 插入数据并设置过期时间为30秒
    redis_manager.insert_with_expiration("testKey", "testValue", 30)

    # 获取并打印值
    value = redis_manager.get("testKey")
    print(f"Inserted value: {value}")

    # 删除数据
    redis_manager.delete("testKey")

    # 尝试获取已删除的键的值
    value_after_deletion = redis_manager.get("testKey")
    print(f"Value after deletion: {value_after_deletion}")
