# theme_manager.py
"""
医学图像处理应用主题管理模块
================================

该模块实现了应用程序的深色/浅色主题切换功能，为用户提供舒适的视觉体验，
特别适合长时间使用的医学图像处理环境。模块通过动态修改Qt样式表实现主题切换。

主要功能：
- 深色/浅色主题切换
- 样式表动态加载与应用
- 主题状态管理与查询

设计特点：
- 采用基于CSS的样式管理，便于维护和扩展
- 支持运行时主题切换，无需重启应用
- 针对医学图像显示优化颜色方案，减少视觉疲劳

作者：[作者名]
创建时间：[日期]
版本：1.0
"""

from PyQt5.QtWidgets import QApplication
import os

class ThemeManager:
    """
    应用程序主题管理器类
    
    负责管理应用程序的整体视觉主题，支持深色和浅色两种模式切换，
    通过修改Qt样式表实现界面元素的视觉风格变化。该类采用单例模式思想，
    保证整个应用中主题状态的一致性。
    """
    
    def __init__(self):
        """
        初始化主题管理器实例
        
        设置默认主题为深色模式，并加载基础样式表文件以备后续使用。
        """
        self.is_dark_mode = True                    # 当前主题状态标识，True为深色模式
        self.base_stylesheet = ""                   # 基础样式表内容缓存
        self.load_base_stylesheet()
    
    def load_base_stylesheet(self):
        """
        加载基础样式表文件
        
        从项目目录中读取styles.css文件内容作为基础样式表，
        该样式表定义了应用的基本视觉风格，主题切换时以此为基础进行调整。
        若文件不存在则使用空样式表并输出提示信息。
        """
        try:
            with open("styles.css", "r", encoding="utf-8") as file:
                self.base_stylesheet = file.read()
        except FileNotFoundError:
            print("未找到 styles.css 文件，使用默认样式")
            self.base_stylesheet = ""
    
    def apply_dark_theme(self):
        """
        应用深色主题
        
        将应用程序界面设置为深色主题模式，该模式采用深色背景和浅色文字，
        有助于减少用户在长时间使用时的眼部疲劳，特别适合医学图像处理场景。
        深色主题基于基础样式表并添加特定的补充样式实现。
        """
        app = QApplication.instance()
        if app:
            # 深色主题就是原始的styles.css样式，附加深色主题专有样式
            dark_stylesheet = self.base_stylesheet + self.get_dark_theme_additions()
            app.setStyleSheet(dark_stylesheet)
    
    def apply_light_theme(self):
        """
        应用浅色主题
        
        将应用程序界面设置为浅色主题模式，该模式采用浅色背景和深色文字，
        适合在明亮环境下使用。通过替换基础样式表中的颜色值实现浅色效果，
        并附加浅色主题专有样式确保界面元素的一致性。
        """
        app = QApplication.instance()
        if app:
            # 基于原始样式表创建浅色主题，使用更柔和的灰色调替换深色调
            light_stylesheet = self.base_stylesheet.replace("#121212", "#e0e0e0")\
                                                  .replace("#1a1a1a", "#d0d0d0")\
                                                  .replace("#e1e1e1", "#444444")\
                                                  .replace("#333333", "#bbbbbb")\
                                                  .replace("#2a2a2a", "#e8e8e8")\
                                                  .replace("#3d3d3d", "#bbbbbb")
            light_stylesheet += self.get_light_theme_additions()
            app.setStyleSheet(light_stylesheet)
    
    def get_dark_theme_additions(self):
        """
        获取深色主题补充样式
        
        返回深色主题模式下的额外样式定义，这些样式不包含在基础样式表中，
        或需要特殊处理的部分。补充样式主要定义主窗口背景等关键元素的深色风格。
        
        Returns:
            str: 深色主题补充CSS样式字符串
        """
        return """
        /* 深色主题补充样式 */
        QMainWindow {
            background-color: #121212;
        }
        """
    
    def get_light_theme_additions(self):
        """
        获取浅色主题补充样式
        
        返回浅色主题模式下的额外样式定义，包括窗口背景、标签颜色等元素的浅色适配，
        特别处理了下拉框选项文字颜色等细节，确保在浅色背景下依然具有良好的可读性。
        
        Returns:
            str: 浅色主题补充CSS样式字符串
        """
        return """
        /* 浅色主题补充样式 */
        QMainWindow {
            background-color: #e0e0e0;
        }
        QLabel[objectName="lab1_foreground"] {
            background-color: #e8e8e8;
        }
        QLabel[objectName="lab2_foreground"] {
            background-color: #e8e8e8;
        }
        QLabel[objectName="lab3_foreground"] {
            background-color: #e8e8e8;
        }
        QFrame#frame1 {
            background-color: #e8e8e8;
        }
        /* 修改滑块控件标签颜色为深蓝色 */
        QLabel#axial_label,
        QLabel#sagittal_label,
        QLabel#coronal_label,
        QLabel#window_width_label,
        QLabel#window_possion_label {
            color: #000000;  
        }
        /* 浅色模式下拉框选项文字颜色设置为黑色 */
        QComboBox QAbstractItemView {
            color: #000000;
        }
        QComboBox QAbstractItemView::item {
            color: #000000;
        }
        CustomComboBox QAbstractItemView {
            color: #000000;
        }
        CustomComboBox QAbstractItemView::item {
            color: #000000;
        }
        QComboBox#suanfa QAbstractItemView {
            color: #000000;
        }
        QComboBox#suanfa QAbstractItemView::item {
            color: #000000;
        }
        QComboBox#sk QAbstractItemView {
            color: #000000;
        }
        QComboBox#sk QAbstractItemView::item {
            color: #000000;
        }
        QComboBox#postprocessing_combo QAbstractItemView {
            color: #000000;
        }
        QComboBox#postprocessing_combo QAbstractItemView::item {
            color: #000000;
        }
        """
    
    def toggle_theme(self):
        """
        切换应用程序主题
        
        在深色和浅色主题之间进行切换，根据当前主题状态自动切换到另一种主题，
        并更新主题状态标识。此方法提供了一键切换主题的便捷功能。
        """
        if self.is_dark_mode:
            self.apply_light_theme()
            self.is_dark_mode = False
        else:
            self.apply_dark_theme()
            self.is_dark_mode = True
    
    def get_current_theme(self):
        """
        获取当前主题状态
        
        返回当前应用程序所使用的主题模式标识，便于其他模块根据主题状态
        进行相应的处理或判断。
        
        Returns:
            str: 当前主题模式，"dark"表示深色模式，"light"表示浅色模式
        """
        return "dark" if self.is_dark_mode else "light"