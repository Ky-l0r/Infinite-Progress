import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

class GradeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("学生成绩追踪系统")
        self.root.geometry("1000x700")
        
        # 数据库初始化
        self.db_path = "student_grades.db"
        self.init_database()
        
        # 创建GUI界面
        self.create_widgets()
        
    def init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # 创建表存储学生成绩
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                score REAL NOT NULL,
                exam_date TEXT NOT NULL,
                exam_name TEXT
            )
        ''')
        
        self.conn.commit()
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置行和列的权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 顶部按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 导入Excel按钮
        import_btn = ttk.Button(button_frame, text="导入Excel成绩表", command=self.import_excel)
        import_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 学生选择下拉框
        ttk.Label(button_frame, text="选择学生:").pack(side=tk.LEFT, padx=(20, 5))
        self.student_var = tk.StringVar()
        self.student_combo = ttk.Combobox(button_frame, textvariable=self.student_var, width=20)
        self.student_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.student_combo.bind("<<ComboboxSelected>>", self.on_student_selected)
        
        # 刷新学生列表按钮
        refresh_btn = ttk.Button(button_frame, text="刷新学生列表", command=self.load_students)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 成绩统计信息区域
        stats_frame = ttk.LabelFrame(main_frame, text="成绩统计", padding="10")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 统计信息标签
        self.stats_labels = {}
        stats_info = [
            ("平均分", "avg_score"),
            ("最高分", "max_score"),
            ("最低分", "min_score"),
            ("总测试次数", "total_tests")
        ]
        
        for i, (text, key) in enumerate(stats_info):
            frame = ttk.Frame(stats_frame)
            frame.grid(row=0, column=i, padx=20, sticky=tk.W)
            label_title = ttk.Label(frame, text=text + ":", font=("Arial", 10, "bold"))
            label_title.pack(anchor=tk.W)
            label_value = ttk.Label(frame, text="0.0", font=("Arial", 10))
            label_value.pack(anchor=tk.W)
            self.stats_labels[key] = label_value
        
        # 图表显示区域
        self.plot_frame = ttk.LabelFrame(main_frame, text="成绩趋势图", padding="5")
        self.plot_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # 成绩列表区域
        list_frame = ttk.LabelFrame(main_frame, text="成绩详情", padding="5")
        list_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        main_frame.columnconfigure(1, weight=1)
        
        # 创建成绩列表
        columns = ("姓名", "科目", "成绩", "日期", "考试名称")
        self.grade_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # 设置列标题
        for col in columns:
            self.grade_tree.heading(col, text=col)
            self.grade_tree.column(col, width=100)
        
        # 添加滚动条
        tree_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.grade_tree.yview)
        self.grade_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.grade_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 初始化图表区域
        self.fig, self.ax = plt.subplots(figsize=(8, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 加载学生列表
        self.load_students()
        
    def import_excel(self):
        """导入Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls")]
        )
        
        if not file_path:
            return
            
        try:
            # 读取Excel文件 - 修改以支持多种格式
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_path.endswith('.xls'):
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                # 自动检测引擎
                df = pd.read_excel(file_path)
            
            # 检查必需的列
            required_columns = ['姓名', '科目', '成绩', '日期']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("错误", f"Excel文件必须包含以下列: {required_columns}")
                return
            
            # 连接到数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 插入数据到数据库
            for index, row in df.iterrows():
                # 检查是否已存在相同记录
                cursor.execute('''
                    SELECT id FROM grades 
                    WHERE student_name=? AND subject=? AND score=? AND exam_date=?
                ''', (row['姓名'], row['科目'], row['成绩'], str(row['日期'])))
                
                if not cursor.fetchone():
                    exam_name = row.get('考试名称', '未知考试') if '考试名称' in df.columns else '未知考试'
                    cursor.execute('''
                        INSERT INTO grades (student_name, subject, score, exam_date, exam_name)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (row['姓名'], row['科目'], row['成绩'], str(row['日期']), exam_name))
            
            conn.commit()
            conn.close()
            
            messagebox.showinfo("成功", f"成功导入 {len(df)} 条成绩记录")
            
            # 刷新学生列表
            self.load_students()
            
        except Exception as e:
            messagebox.showerror("错误", f"导入Excel文件时出错: {str(e)}")
    
    def load_students(self):
        """加载学生列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取所有学生姓名（去重）
            cursor.execute("SELECT DISTINCT student_name FROM grades WHERE subject='技术' ORDER BY student_name")
            students = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # 更新下拉框选项
            self.student_combo['values'] = students
            
            # 如果当前没有选择学生，选择第一个
            if students and not self.student_var.get():
                self.student_var.set(students[0])
                self.on_student_selected(None)
                
        except Exception as e:
            messagebox.showerror("错误", f"加载学生列表时出错: {str(e)}")
    
    def on_student_selected(self, event):
        """当选择学生时更新图表和成绩列表"""
        student_name = self.student_var.get()
        if student_name:
            self.update_student_data(student_name)
    
    def update_student_data(self, student_name):
        """更新学生数据（图表和列表）"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 获取学生技术科目的成绩数据
            query = """
                SELECT student_name, subject, score, exam_date, exam_name 
                FROM grades 
                WHERE student_name=? AND subject='技术'
                ORDER BY exam_date
            """
            df = pd.read_sql_query(query, conn, params=(student_name,))
            
            conn.close()
            
            # 更新成绩列表
            for item in self.grade_tree.get_children():
                self.grade_tree.delete(item)
                
            for _, row in df.iterrows():
                self.grade_tree.insert("", "end", values=list(row))
            
            # 计算统计信息
            if not df.empty:
                avg_score = df['score'].mean()
                max_score = df['score'].max()
                min_score = df['score'].min()
                total_tests = len(df)
                
                # 更新统计标签
                self.stats_labels['avg_score'].config(text=f"{avg_score:.2f}")
                self.stats_labels['max_score'].config(text=f"{max_score:.2f}")
                self.stats_labels['min_score'].config(text=f"{min_score:.2f}")
                self.stats_labels['total_tests'].config(text=f"{total_tests}")
                
                # 绘制成绩趋势图
                self.ax.clear()
                
                if len(df) > 0:
                    # 将日期转换为适当的格式
                    df['exam_date'] = pd.to_datetime(df['exam_date'])
                    
                    # 绘制折线图
                    self.ax.plot(df['exam_date'], df['score'], marker='o', linewidth=2, markersize=8)
                    self.ax.set_title(f"{student_name} - 技术科目成绩趋势")
                    self.ax.set_xlabel("考试日期")
                    self.ax.set_ylabel("成绩")
                    self.ax.grid(True, linestyle='--', alpha=0.6)
                    
                    # 旋转x轴标签以避免重叠
                    self.ax.tick_params(axis='x', rotation=45)
                    
                    # 调整布局
                    self.fig.tight_layout()
                
                self.canvas.draw()
            else:
                # 如果没有数据，清空图表和统计信息
                self.ax.clear()
                self.ax.text(0.5, 0.5, '没有找到该学生的成绩数据', 
                            horizontalalignment='center', verticalalignment='center',
                            transform=self.ax.transAxes, fontsize=14)
                self.ax.set_xlim(0, 1)
                self.ax.set_ylim(0, 1)
                self.ax.set_title(f"{student_name} - 技术科目成绩趋势")
                self.canvas.draw()
                
                # 清空统计信息
                for label in self.stats_labels.values():
                    label.config(text="0.0")
        
        except Exception as e:
            messagebox.showerror("错误", f"更新学生数据时出错: {str(e)}")


def main():
    root = tk.Tk()
    app = GradeTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()