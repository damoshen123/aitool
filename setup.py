#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
完整的部署脚本，包含所有依赖
"""
import subprocess
import sys
import os
import platform

def get_platform_info():
    """获取平台信息"""
    system = platform.system()
    return {
        'is_windows': system == 'Windows',
        'is_linux': system == 'Linux', 
        'is_mac': system == 'Darwin',
        'system': system
    }

def check_and_install_venv():
    """检查并安装venv模块（Linux）"""
    platform_info = get_platform_info()
    
    if platform_info['is_linux']:
        # 检查是否可以导入venv
        try:
            import venv
            return True
        except ImportError:
            print("\n检测到缺少python3-venv包...")
            
            # 获取Python版本
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            
            # 尝试自动安装
            print(f"尝试安装python{python_version}-venv...")
            
            # 检查是否有sudo权限
            try:
                # 首先更新包列表
                subprocess.run(["sudo", "apt", "update"], check=True)
                # 安装venv包
                result = subprocess.run(
                    ["sudo", "apt", "install", "-y", f"python{python_version}-venv"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("✓ python3-venv安装成功！")
                    return True
                else:
                    print(f"安装失败: {result.stderr}")
            except subprocess.CalledProcessError:
                pass
            
            # 如果自动安装失败，提供手动安装指令
            print("\n请手动安装python3-venv包：")
            print(f"  Ubuntu/Debian: sudo apt install python{python_version}-venv")
            print(f"  CentOS/RHEL: sudo yum install python3-devel")
            print(f"  Fedora: sudo dnf install python3-devel")
            print("\n安装完成后，请重新运行此脚本。")
            return False
    
    return True

def create_virtual_env():
    """创建虚拟环境"""
    # 先检查Linux系统是否有venv
    if not check_and_install_venv():
        sys.exit(1)
    
    print("正在创建虚拟环境...")
    subprocess.check_call([sys.executable, "-m", "venv", "venv"])
    
    platform_info = get_platform_info()
    if platform_info['is_windows']:
        python_exe = os.path.abspath(os.path.join("venv", "Scripts", "python.exe"))
        pip_exe = os.path.abspath(os.path.join("venv", "Scripts", "pip.exe"))
    else:
        python_exe = os.path.abspath(os.path.join("venv", "bin", "python"))
        pip_exe = os.path.abspath(os.path.join("venv", "bin", "pip"))
    
    return python_exe, pip_exe

def check_existing_venv():
    """检查是否已存在虚拟环境"""
    platform_info = get_platform_info()
    if platform_info['is_windows']:
        python_exe = os.path.join("venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join("venv", "bin", "python")
    
    return os.path.exists(python_exe)

def get_venv_paths():
    """获取虚拟环境路径"""
    platform_info = get_platform_info()
    if platform_info['is_windows']:
        python_exe = os.path.abspath(os.path.join("venv", "Scripts", "python.exe"))
        pip_exe = os.path.abspath(os.path.join("venv", "Scripts", "pip.exe"))
    else:
        python_exe = os.path.abspath(os.path.join("venv", "bin", "python"))
        pip_exe = os.path.abspath(os.path.join("venv", "bin", "pip"))
    
    return python_exe, pip_exe

def test_import(python_exe, module_name):
    """测试模块是否可以导入"""
    try:
        result = subprocess.run(
            [python_exe, "-c", f"import {module_name}"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def check_system_dependencies():
    """检查系统依赖（Linux）"""
    platform_info = get_platform_info()
    
    if platform_info['is_linux']:
        print("\n检查系统依赖...")
        
        # 检查是否安装了portaudio（pyaudio需要）
        try:
            result = subprocess.run(["pkg-config", "--exists", "portaudio-2.0"], capture_output=True)
            if result.returncode != 0:
                print("\n⚠ 检测到缺少portaudio库（pyaudio需要）")
                print("请安装：sudo apt-get install portaudio19-dev")
        except:
            pass
        
        # 检查是否安装了ffmpeg（音频处理可能需要）
        try:
            result = subprocess.run(["which", "ffmpeg"], capture_output=True)
            if result.returncode != 0:
                print("\n⚠ 建议安装ffmpeg以获得更好的音频支持")
                print("请安装：sudo apt-get install ffmpeg")
        except:
            pass

def install_pytorch(python_exe, pip_exe, platform_info):
    """专门安装PyTorch及相关组件"""
    print("\n2. 安装 PyTorch 套件...")
    
    # 首先清理可能存在的损坏安装
    print("   清理旧版本...")
    for pkg in ["torch", "torchvision", "torchaudio"]:
        subprocess.run([pip_exe, "uninstall", "-y", pkg], capture_output=True)
    
    # 根据平台选择安装命令
    if platform_info['is_windows']:
        # Windows使用CPU版本
        install_commands = [
            [pip_exe, "install", "torch==2.0.1+cpu", "torchvision==0.15.2+cpu", "torchaudio==2.0.2+cpu", 
             "-f", "https://download.pytorch.org/whl/torch_stable.html"],
            [pip_exe, "install", "torch", "torchvision", "torchaudio", 
             "--index-url", "https://download.pytorch.org/whl/cpu"]
        ]
    else:
        # Linux/Mac - 使用CPU版本以减小体积
        install_commands = [
            [pip_exe, "install", "torch", "torchvision", "torchaudio", 
             "--index-url", "https://download.pytorch.org/whl/cpu"],
            [pip_exe, "install", "torch==2.0.1", "torchvision==0.15.2", "torchaudio==2.0.2"]
        ]
    
    # 尝试不同的安装方案
    success = False
    for i, cmd in enumerate(install_commands):
        print(f"   尝试方案 {i+1}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                # 验证安装
                if all(test_import(python_exe, mod) for mod in ["torch", "torchvision", "torchaudio"]):
                    print("   ✓ PyTorch安装成功")
                    success = True
                    break
                else:
                    print("   安装完成但导入失败，尝试下一个方案...")
            else:
                print(f"   安装失败: {result.stderr[:200]}...")
        except Exception as e:
            print(f"   出错: {e}")
    
    # 如果都失败了，尝试分别安装
    if not success:
        print("   尝试单独安装各组件...")
        for pkg in ["torch", "torchvision", "torchaudio"]:
            print(f"   安装 {pkg}...")
            try:
                subprocess.check_call([pip_exe, "install", pkg])
            except:
                print(f"   {pkg} 安装失败，继续...")
    
    # 最终验证
    torch_ok = test_import(python_exe, "torch")
    torchaudio_ok = test_import(python_exe, "torchaudio")
    
    if torch_ok and torchaudio_ok:
        print("   ✓ PyTorch核心组件安装成功")
        return True
    else:
        print("   ⚠ PyTorch安装可能不完整")
        if not torch_ok:
            print("     - torch 导入失败")
        if not torchaudio_ok:
            print("     - torchaudio 导入失败")
        return False

def install_all_dependencies(python_exe, pip_exe):
    """安装所有依赖"""
    platform_info = get_platform_info()
    
    # 检查系统依赖
    if platform_info['is_linux']:
        check_system_dependencies()
    
    # 升级pip
    print("\n1. 升级pip...")
    try:
        subprocess.check_call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])
    except:
        print("   pip升级失败，使用当前版本继续")
    
    # 安装PyTorch
    pytorch_success = install_pytorch(python_exe, pip_exe, platform_info)
    
    # 安装其他依赖
    print("\n3. 安装其他依赖...")
    
    # 基础依赖
    basic_deps = ["requests", "pygame", "wave"]
    for dep in basic_deps:
        print(f"   安装 {dep}...")
        try:
            subprocess.check_call([pip_exe, "install", dep])
            print(f"   ✓ {dep}")
        except:
            print(f"   ✗ {dep} 安装失败")
    
    # 安装funasr（需要torch）
    if pytorch_success:
        print(f"   安装 funasr...")
        try:
            subprocess.check_call([pip_exe, "install", "funasr"])
            print(f"   ✓ funasr")
        except:
            print(f"   ✗ funasr 安装失败")
    else:
        print("   ⚠ 跳过 funasr（需要PyTorch）")
    
    # 安装语音识别相关
    print(f"   安装 SpeechRecognition...")
    try:
        subprocess.check_call([pip_exe, "install", "SpeechRecognition"])
        print(f"   ✓ SpeechRecognition")
    except:
        print(f"   ✗ SpeechRecognition 安装失败")
    
    # pyaudio可能需要特殊处理
    print(f"   安装 pyaudio...")
    try:
        subprocess.check_call([pip_exe, "install", "pyaudio"])
        print(f"   ✓ pyaudio")
    except:
        print(f"   ✗ pyaudio 安装失败（语音输入可能受影响）")
        if platform_info['is_linux']:
            print("     提示：请先安装 sudo apt-get install portaudio19-dev")
    
    # 安装dashscope
    print(f"   安装 dashscope...")
    try:
        subprocess.check_call([pip_exe, "install", "dashscope"])
        print(f"   ✓ dashscope")
    except:
        print(f"   ✗ dashscope 安装失败")
    
    # 最终验证
    print("\n4. 验证核心依赖...")
    core_modules = {
        "torch": "PyTorch",
        "torchaudio": "TorchAudio",
        "funasr": "FunASR",
        "speech_recognition": "SpeechRecognition",
        "dashscope": "DashScope",
        "pygame": "Pygame",
        "requests": "Requests"
    }
    
    all_ok = True
    for module, name in core_modules.items():
        if test_import(python_exe, module):
            print(f"   ✓ {name}")
        else:
            print(f"   ✗ {name}")
            all_ok = False
    
    if not all_ok:
        print("\n⚠ 部分依赖安装失败，程序可能无法正常运行")
        print("建议手动检查并安装缺失的依赖")
    else:
        print("\n✓ 所有核心依赖安装成功！")
    
    return all_ok

def find_main_script():
    """查找主程序文件"""
    # 可能的主程序文件名
    possible_names = ["main.py", "voice_assistant.py", "wake_word.py", "app.py"]
    
    for name in possible_names:
        if os.path.exists(name):
            return name
    
    # 查找包含wake_word_detection的文件
    py_files = [f for f in os.listdir('.') if f.endswith('.py') and f not in ['setup.py', 'setup_complete.py']]
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'wake_word_detection' in content and 'def wake_word_detection' in content:
                    return py_file
        except:
            continue
    
    return None

def run_program(python_exe):
    """运行主程序"""
    main_script = find_main_script()
    
    if not main_script:
        print("\n错误：找不到主程序文件！")
        print("请确保主程序文件在当前目录")
        
        # 列出所有Python文件供用户选择
        py_files = [f for f in os.listdir('.') if f.endswith('.py')]
        if py_files:
            print("\n当前目录的Python文件：")
            for i, f in enumerate(py_files):
                print(f"{i+1}. {f}")
            
            try:
                choice = input("\n请输入要运行的文件编号（直接回车退出）: ").strip()
                if choice:
                    main_script = py_files[int(choice)-1]
            except:
                return
    
    if main_script:
        print(f"\n正在运行: {main_script}")
        try:
            result = subprocess.call([python_exe, main_script])
            if result != 0:
                print(f"\n程序退出，返回码: {result}")
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as e:
            print(f"\n运行出错: {e}")

def show_instructions():
    """显示使用说明"""
    platform_info = get_platform_info()
    
    print("\n=== 使用说明 ===")
    if platform_info['is_windows']:
        print("激活虚拟环境: venv\\Scripts\\activate")
        print("运行程序: python main.py (激活后)")
        print("或直接运行: venv\\Scripts\\python.exe main.py")
    else:
        print("激活虚拟环境: source venv/bin/activate")
        print("运行程序: python main.py (激活后)")
        print("或直接运行: venv/bin/python main.py")

def main():
    """主函数"""
    print("=== AI助手完整安装程序 ===\n")
    
    # 切换到脚本目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if script_dir:
        os.chdir(script_dir)
    
    print(f"工作目录: {os.getcwd()}")
    platform_info = get_platform_info()
    print(f"操作系统: {platform_info['system']}")
    print(f"Python版本: {sys.version}")
    
    # 检查是否已有虚拟环境
    if check_existing_venv():
        use_existing = input("\n检测到已存在虚拟环境，是否使用？(y/n，默认y): ").strip().lower()
        if use_existing == 'n':
            print("删除旧环境...")
            import shutil
            shutil.rmtree("venv")
            # 创建新环境
            python_exe, pip_exe = create_virtual_env()
            install_all_dependencies(python_exe, pip_exe)
        else:
            # 使用现有环境
            python_exe, pip_exe = get_venv_paths()
            print("使用现有虚拟环境")
            
            # 检查是否需要安装依赖
            check_deps = input("是否检查并安装缺失的依赖？(y/n，默认n): ").strip().lower()
            if check_deps == 'y':
                install_all_dependencies(python_exe, pip_exe)
    else:
        # 创建新环境
        python_exe, pip_exe = create_virtual_env()
        install_all_dependencies(python_exe, pip_exe)
    
    # 创建必要目录
    os.makedirs("voices", exist_ok=True)
    
    print("\n=== 安装完成 ===")
    
    # 显示使用说明
    show_instructions()
    
    # 询问是否运行
    run_now = input("\n是否立即运行程序? (y/n，默认y): ").strip().lower()
    if run_now != 'n':
        run_program(python_exe)
    else:
        print("\n安装完成！您可以随时运行程序。")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n安装被用户取消")
    except Exception as e:
        print(f"\n\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
