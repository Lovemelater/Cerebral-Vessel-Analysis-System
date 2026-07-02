import sys
import importlib
import subprocess
import pkg_resources

def check_python_version():
    """检查Python版本"""
    return sys.version

def check_package_version(package_name):
    """检查指定包的版本"""
    try:
        # 尝试直接导入模块并检查版本
        module = importlib.import_module(package_name)
        if hasattr(module, '__version__'):
            return module.__version__
        elif package_name == 'torch':  # 特殊处理PyTorch
            return module.__version__
        elif package_name == 'SimpleITK':  # 特殊处理SimpleITK
            return module.Version_VersionString()
    except ImportError:
        pass
    
    try:
        # 如果直接导入失败，尝试通过pkg_resources获取版本
        return pkg_resources.get_distribution(package_name).version
    except:
        pass
    
    return "未安装"

def check_cuda_version():
    """检查CUDA版本"""
    try:
        # 尝试通过nvidia-smi命令检查CUDA版本
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            # 从输出中提取CUDA版本
            import re
            match = re.search(r'CUDA Version: (\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    
    try:
        # 尝试通过nvcc命令检查CUDA版本
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            import re
            match = re.search(r'release (\d+\.\d+)', result.stdout)
            if match:
                return match.group(1)
    except:
        pass
    
    try:
        # 尝试通过torch检查CUDA版本
        import torch
        if torch.cuda.is_available():
            return torch.version.cuda
        else:
            return "CUDA不可用"
    except:
        pass
    
    return "无法检测"

def list_all_packages():
    """列出所有已安装的包"""
    try:
        installed_packages = [d for d in pkg_resources.working_set]
        installed_packages_list = sorted([(i.key, i.version) for i in installed_packages])
        return installed_packages_list
    except:
        return []

def main():
    """主函数，检查并打印所有包的版本"""
    print("=" * 50)
    print("Python环境和包版本检测工具")
    print("=" * 50)
    
    # 检查Python版本
    print(f"Python版本: {check_python_version()}")
    
    # 定义需要检查的包列表
    packages_to_check = [
        'SimpleITK',
        'numpy', 
        'torch',
        'PyQt5',
        'tqdm'
    ]
    
    print("\n指定包版本信息:")
    print("-" * 30)
    
    # 检查每个包的版本
    for package in packages_to_check:
        version = check_package_version(package)
        print(f"{package}: {version}")
    
    # 检查CUDA版本
    print(f"CUDA版本: {check_cuda_version()}")
    
    # 列出所有已安装的包
    print("\n所有已安装的包:")
    print("-" * 30)
    all_packages = list_all_packages()
    for package, version in all_packages:
        print(f"{package}: {version}")

if __name__ == "__main__":
    main()