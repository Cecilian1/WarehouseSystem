"""
sensor.py
负责与底层 C 程序（sht31e）通信，实时获取冰箱内的温湿度数据。
使用的是子进程调用（subprocess）的方式，跨平台且易于部署。
"""
import subprocess
import re

# 可执行文件的名称
SHT31_EXECUTABLE = "./sht31e"


def get_temperature_humidity():
    """
    主函数：获取当前温湿度
    返回: (temperature, humidity) 元组，例如 (5.5, 80.0)
    """
    try:
        # 1. 调用底层 C 程序
        # 加上 'p' 参数，让 C 程序去读取温湿度
        # timeout=5 防止 C 程序由于硬件问题死循环卡死你的系统
        result = subprocess.run(
            [SHT31_EXECUTABLE, 'p'],
            capture_output=True,
            text=True,
            timeout=5
        )

        # 2. 检查程序是否正常退出（返回码为 0）
        if result.returncode != 0:
            print(f"SHT31 C程序返回异常代码: {result.returncode}")
            return 5.5, 80.0  # 兜底值

        # 3. 解析 C 程序的打印输出
        # 期望的输出格式类似于：
        # "Temperature 25.50c - 77.90f\nHumidity 80.00%\n"
        output_str = result.stdout

        # 4. 用正则表达式提取温度（匹配数字+单位c）和湿度（匹配数字+%）
        temp_match = re.search(r'Temperature ([\d.]+)c', output_str)
        hum_match = re.search(r'Humidity ([\d.]+)%', output_str)

        if temp_match and hum_match:
            temp = float(temp_match.group(1))
            hum = float(hum_match.group(1))

            # 简单的数据合理性检查（防止传感器读坏了）
            if -30.0 < temp < 50.0 and 0.0 < hum < 100.0:
                print(f"实时传感器数据：温度 {temp} ℃，湿度 {hum} %")
                return temp, hum
            else:
                print(f"传感器数据异常（温度{temp}℃ 或 湿度{hum}% 超出合理范围），使用兜底值")
                return 5.5, 80.0
        else:
            print(f"无法从C程序输出中解析温湿度，原始输出: '{output_str}'")
            return 5.5, 80.0

    except subprocess.TimeoutExpired:
        print("读取传感器超时，使用兜底值")
        return 5.5, 80.0
    except FileNotFoundError:
        print(f"致命错误：找不到可执行文件 {SHT31_EXECUTABLE}！请确认它已在同一目录下。")
        return 5.5, 80.0
    except Exception as e:
        print(f"传感器读取未知异常: {e}")
        return 5.5, 80.0