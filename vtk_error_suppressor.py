import vtk
from contextlib import contextmanager

class VTKErrorSuppressor:
    """
    VTK错误信息抑制器组件
    该组件用于屏蔽VTK的错误和警告信息
    """
    
    def __init__(self):
        """初始化VTK错误抑制器"""
        self._original_error_output = None
        self._original_warning_output = None
        self._error_observers = []
        self._warning_observers = []
        
    def suppress_vtk_errors(self):
        """
        抑制VTK错误信息输出
        """
        # 方法1: 重定向VTK错误输出
        self._original_error_output = vtk.vtkObject.GetGlobalWarningDisplay()
        vtk.vtkObject.GlobalWarningDisplayOff()
        
        # 方法2: 设置VTK输出窗口为NULL
        null_output = vtk.vtkOutputWindow()
        vtk.vtkOutputWindow.SetInstance(null_output)
        
        # 方法3: 设置错误处理回调函数
        def error_handler(obj, event):
            # 静默处理错误，不输出到控制台
            pass
            
        def warning_handler(obj, event):
            # 静默处理警告，不输出到控制台
            pass
        
        # 注册错误和警告观察者
        self._error_observers.append(error_handler)
        self._warning_observers.append(warning_handler)
    
    def restore_vtk_errors(self):
        """
        恢复VTK错误信息输出
        """
        # 恢复原始设置
        if self._original_error_output is not None:
            if self._original_error_output:
                vtk.vtkObject.GlobalWarningDisplayOn()
            else:
                vtk.vtkObject.GlobalWarningDisplayOff()
        
        # 恢复默认输出窗口
        default_output = vtk.vtkOutputWindow()
        vtk.vtkOutputWindow.SetInstance(default_output)
        
        # 清空观察者列表
        self._error_observers.clear()
        self._warning_observers.clear()
    
    @contextmanager
    def suppress_context(self):
        """
        上下文管理器，用于临时抑制VTK错误
        """
        self.suppress_vtk_errors()
        try:
            yield
        finally:
            self.restore_vtk_errors()

# 创建全局实例
vtk_error_suppressor = VTKErrorSuppressor()

def suppress_vtk_warnings():
    """
    全局函数，用于在整个应用程序中抑制VTK警告和错误
    """
    vtk_error_suppressor.suppress_vtk_errors()

def restore_vtk_warnings():
    """
    全局函数，用于恢复VTK警告和错误输出
    """
    vtk_error_suppressor.restore_vtk_errors()