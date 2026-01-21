# main.py

import requests
import json
from config import API_KEY, MODEL_ENDPOINT
from prompts import TIAN_CAI_PERSONA
from database import init_db, save_memory, get_recent_memories, get_user_profile
import tkinter as tk
from tkinter import scrolledtext, Entry, Frame, Label
#调用通义千问API获取回复
def call_qwen(prompt,context=""): 
    # 请求头配置
    headers = {     
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 构建消息历史
    messages = [{"role": "system", "content": TIAN_CAI_PERSONA.strip()}]
    
    # 添加上下文信息（如果有的话）
    if context:
        messages.append({"role": "system", "content": f"上下文信息：{context}"})
    
    # 添加当前用户输入
    messages.append({"role": "user", "content": prompt})
                    
    # 请求数据配置
    data = {
        "model": "qwen-plus-latest",  # 可换为 qwen-turbo（更快更便宜）
        "input": {
            "messages": [
                {"role": "system", "content": TIAN_CAI_PERSONA.strip()},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "temperature": 0.75,
            "top_p": 0.75
        }
    }
    
    try:
        response = requests.post(MODEL_ENDPOINT, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result["output"]["text"]
    except requests.exceptions.RequestException as e:
        return f"请检查网络或API密钥。错误：{e}"
    except KeyError:
        return f"原始响应：{result}"

def build_context():
    """构建上下文信息"""
    # 获取最近的记忆
    recent_memories = get_recent_memories(3)
    memory_context = ""
    if recent_memories:
        memory_context = "最近的对话记录：\n"
        for user_input, ai_response, emotion, category in recent_memories:
            memory_context += f"用户: {user_input}\n天才: {ai_response}\n"
    
    # 获取用户画像
    user_profile = get_user_profile()
    profile_context = ""
    if user_profile["frequent_topics"] or user_profile["common_moods"]:
        profile_context = "用户偏好信息："
        if user_profile["frequent_topics"]:
            topics = "、".join(user_profile["frequent_topics"])
            profile_context += f"经常讨论{topics}；"
        if user_profile["common_moods"]:
            moods = "、".join(user_profile["common_moods"])
            profile_context += f"常见情绪{moods}；"
    
    return memory_context + "\n" + profile_context if profile_context else memory_context

class GUI:
    def __init__(self,root):
        self.root = root
        self.root.title("天才")
        self.root.geometry("800x600")
        self.root.configure(bg="#F0F0F0")
        self.root.resizable(False,False)

        #初始化数据库
        init_db()

        self.setup_ui()

        #显示欢迎信息
        self.display_message("天才", "不和无知者讲话", "left")

    def setup_ui(self):
        #标题栏
        title_frame =Frame(self.root,bg="#6a5acd",height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = Label(title_frame,text="天才",fg="white",bg="#6a5acd",font=("Arial",20,"bold"))
        title_label.pack(pady=15)

        #聊天框
        chat_frame = Frame(self.root,bg="#F0F0F0")
        chat_frame.pack(fill=tk.BOTH,expand=True,padx=10,pady=(10,0))

        self.chat_display = scrolledtext.ScrolledText(chat_frame,bg="#FFFFFF",fg="#333333",font=("Arial",12),padx=15,pady=15)
        self.chat_display.pack(fill=tk.BOTH,expand=True)
        
        #输入框
        input_frame = Frame(self.root,bg="#F0F0F0")
        input_frame.pack(fill=tk.X,padx=10,pady=10)

        self.user_input = Entry(input_frame,bg="#FFFFFF",fg="#000000",font=("Arial",12),relief=tk.FLAT)
        self.user_input.pack(side=tk.LEFT,fill=tk.X,expand=True,ipady=8)
        self.user_input.bind("<Return>",self.send_message)

        send_button = tk.Button(input_frame,text="发送",bg="#6a5acd",fg="white",font=("Arial",12,"bold"),relief=tk.FLAT,padx=20,pady=5,cursor="hand2")
        send_button.pack(side=tk.RIGHT,padx=(10,0),ipady=3)

        #绑定关闭组件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    #发送消息
    def send_message(self,event=None):
        user_text = self.user_input.get().strip()
        if not user_text:
            return

        if user_text.lower() in ['exit', 'quit', '退出']:
            self.on_closing()
            return

        #显示用户消息
        self.display_message("你", user_text, "right")
        self.user_input.delete(0,tk.END)

        # 构建上下文
        context = build_context()

        # 调用通义千问API获取回复
        self.root.update()  #更新界面
        ai_response = call_qwen(user_text, context)

        # 显示回复
        self.display_message("天才", ai_response, "left")

        #保存记忆
        save_memory(user_text,ai_response)

    #显示消息
    def display_message(self,sender,message,align):
        self.chat_display.config(state=tk.NORMAL)

        #配置标签样式
        if align == "right":
            tag_name = "user"
            self.chat_display.tag_configure(tag_name, justify=tk.RIGHT, foreground="#0078d7")
        else:
            tag_name = "ai"
            self.chat_display.tag_configure(tag_name, justify=tk.LEFT, foreground="#333333")

        #插入消息
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n", tag_name)

        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.yview(tk.END)  # 滚动到底部
        #关闭程序时处理
    def on_closing(self):
        self.root.destroy()

def main():
    #欢迎语
    print("\n" + "="*30)
    print("           欢迎回来")
    print("         天才」已上线")
    print("="*30 + "\n")
    print("（输入 'exit' 或 'quit' 退出）\n")

    while True:
        user_input = input("你: ").strip()
        if user_input.lower() in ['exit', 'quit', '退出']:
            print("\n再见，路边。\n")
            break
        
        if not user_input:
            continue
            
        # 构建上下文
        context = build_context()

        print("天才: ", end="", flush=True)
        response = call_qwen(user_input)
        print(response)
        print()

        # 保存记忆（这里简化处理，实际应用中可以更智能地分析情绪和分类）
        save_memory(user_input, response)

def main_gui():
    root = tk.Tk()
    app = GUI(root)
    root.mainloop()

if __name__ == "__main__":
    import sys
    # 默认运行 GUI 模式，除非明确指定 --cli 参数
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main()  # 运行命令行模式
    else:
        main_gui()  # 默认运行 GUI 模式