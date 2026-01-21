# database.py
# 记忆系统

import sqlite3
import os
from datetime import datetime

DB_PATH = "data/memory.db"

def init_db():
    """初始化记忆数据库"""
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            user_input TEXT,
            ai_response TEXT,
            emotion_tag TEXT,  -- happy, sad, tired, excited...
            category TEXT      -- work, life, hobby, health...
        )
    ''')
    conn.commit()
    conn.close()

def save_memory(user_input, ai_response, emotion_tag="", category="general"):
    """保存一次对话记忆"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO memories (timestamp, user_input, ai_response, emotion_tag, category)
        VALUES (?, ?, ?, ?, ?)
    ''', (datetime.now().isoformat(), user_input, ai_response, emotion_tag, category))
    conn.commit()
    conn.close()

def get_recent_memories(limit=5):
    """获取最近的记忆"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT user_input, ai_response, emotion_tag, category 
        FROM memories 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_profile():
    """生成用户画像（简化版）"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT category, emotion_tag, COUNT(*) 
        FROM memories 
        GROUP BY category, emotion_tag 
        ORDER BY COUNT(*) DESC 
        LIMIT 3
    ''')
    top = c.fetchall()
    conn.close()
    
    profile = {"frequent_topics": [], "common_moods": []}
    for cat, emo, cnt in top:
        if cat != "general":
            profile["frequent_topics"].append(cat)
        if emo:
            profile["common_moods"].append(emo)
    
    return profile