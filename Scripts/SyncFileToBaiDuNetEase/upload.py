#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件上传脚本
支持上传单个文件或整个文件夹（递归）到百度网盘指定目录
"""

import os
import sys
import json
import argparse
import subprocess
import shutil
from datetime import datetime
from pathlib import Path


def check_baidupcs_go():
    """检查 BaiduPCS-Go 是否已安装"""
    possible_names = ['BaiduPCS-Go', 'baidupcs-go', 'baidupcs']
    
    for cmd in possible_names:
        if shutil.which(cmd):
            return cmd
    
    return None


def check_remote_directory_exists(cmd, remote_dir):
    """
    检查远端目录是否存在
    
    Args:
        cmd: BaiduPCS-Go 命令
        remote_dir: 远端目录路径
        
    Returns:
        bool: 目录是否存在
    """
    try:
        # 使用 ls 命令检查目录
        result = subprocess.run(
            [cmd, 'ls', remote_dir],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 如果返回码为0，说明目录存在
        return result.returncode == 0
    except:
        return False


def list_remote_directory(cmd, remote_dir):
    """
    列出远端目录的内容
    
    Args:
        cmd: BaiduPCS-Go 命令
        remote_dir: 远端目录路径
        
    Returns:
        list: 目录项列表，每个元素为 {'name': 名称, 'type': 'dir'/'file', 'path': 完整路径}
    """
    try:
        result = subprocess.run(
            [cmd, 'ls', remote_dir],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode != 0:
            print(f"警告：列出远端目录失败: {result.stderr}")
            return []
        
        items = []
        lines = result.stdout.strip().split('\n')
        
        # 确保 remote_dir 格式正确
        remote_dir_clean = remote_dir.rstrip('/')
        
        # 解析 ls 输出
        # BaiduPCS-Go 输出格式示例：
        # 当前目录: /TestUpload
        # ----
        #   #   文件大小        修改日期               文件(目录)         
        #   0           -  2026-01-17 23:55:09  Test1/                    
        #   1           -  2026-01-18 00:00:14  Test2/                    
        #   2      6.94KB  2026-01-18 00:01:40  cookies.json              
        #      总: 6.94KB                       文件总数: 1, 目录总数: 2  
        # ----
        
        import re
        
        # 日期时间模式：YYYY-MM-DD HH:MM:SS
        date_time_pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
        
        in_data_section = False
        for line in lines:
            line_original = line  # 保留原始行用于调试
            line = line.rstrip()  # 只去除右侧空白，保留左侧空格（用于对齐判断）
            
            # 跳过空行
            if not line.strip():
                continue
            
            # 检测数据区域开始（分隔线）
            if line.strip().startswith('----'):
                in_data_section = True
                continue
            
            # 跳过标题行
            if ('当前目录:' in line or '文件大小' in line or 
                '修改日期' in line or '文件(目录)' in line or
                line.strip().startswith('#')):
                continue
            
            # 跳过统计行
            if '总:' in line or '文件总数:' in line or '目录总数:' in line:
                continue
            
            # 只在数据区域内解析
            if not in_data_section:
                continue
            
            # 查找日期时间模式
            match = re.search(date_time_pattern, line)
            if not match:
                continue
            
            # 日期时间之后的所有内容就是文件名/目录名
            date_time_end = match.end()
            name_with_trailing = line[date_time_end:].strip()
            
            # 去除末尾的空白字符，但保留文件名中的空格和特殊字符
            name_with_slash = name_with_trailing.rstrip()
            
            if not name_with_slash:
                continue
            
            # 判断是目录还是文件：如果以 / 结尾，则是目录
            is_dir = name_with_slash.endswith('/')
            name = name_with_slash.rstrip('/')
            
            if name:
                # 构建完整路径
                full_path = f"{remote_dir_clean}/{name}"
                
                items.append({
                    'name': name,
                    'type': 'dir' if is_dir else 'file',
                    'path': full_path
                })
        
        return items
    except Exception as e:
        print(f"警告：列出远端目录时出错: {e}")
        return []


def get_remote_subdirectories(cmd, remote_dir, recursive=True):
    """
    递归获取远端目录下的所有子文件夹
    只返回叶子文件夹（没有子文件夹的文件夹）
    
    Args:
        cmd: BaiduPCS-Go 命令
        remote_dir: 远端目录路径
        recursive: 是否递归查询
        
    Returns:
        list: 叶子子文件夹路径列表（只包含没有子文件夹的文件夹）
    """
    leaf_dirs = []
    
    def _get_leaf_dirs(current_dir):
        """递归获取叶子目录（没有子文件夹的目录）"""
        items = list_remote_directory(cmd, current_dir)
        
        # 检查当前目录下是否有子文件夹
        has_subdirs = False
        subdirs_in_current = []
        
        for item in items:
            if item['type'] == 'dir':
                has_subdirs = True
                subdirs_in_current.append(item['path'])
        
        if not has_subdirs:
            # 当前目录是叶子目录（没有子文件夹），添加到结果
            if current_dir != remote_dir:  # 不包含根目录本身
                leaf_dirs.append(current_dir)
        else:
            # 当前目录有子文件夹，递归查询子目录
            if recursive:
                for subdir in subdirs_in_current:
                    _get_leaf_dirs(subdir)
    
    _get_leaf_dirs(remote_dir)
    return leaf_dirs


def upload_file(cmd, local_path, remote_dir, overwrite=True):
    """
    上传单个文件
    
    Args:
        cmd: BaiduPCS-Go 命令
        local_path: 本地文件路径
        remote_dir: 远端目标目录
        overwrite: 是否覆盖同名文件
        
    Returns:
        tuple: (是否成功, 错误信息)
    """
    try:
        # 构建上传命令
        upload_cmd = [cmd, 'upload']
        
        # 如果支持覆盖策略，添加参数
        # 注意：不同版本的 BaiduPCS-Go 可能参数不同，这里先尝试基本命令
        upload_cmd.append(local_path)
        upload_cmd.append(remote_dir)
        
        result = subprocess.run(
            upload_cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return False, error_msg
            
    except Exception as e:
        return False, str(e)


def get_relative_path(local_file, local_base):
    """
    获取文件相对于基础目录的相对路径
    
    Args:
        local_file: 本地文件完整路径
        local_base: 本地基础目录路径
        
    Returns:
        str: 相对路径
    """
    local_file = Path(local_file).resolve()
    local_base = Path(local_base).resolve()
    
    try:
        return str(local_file.relative_to(local_base))
    except ValueError:
        # 如果文件不在基础目录下，返回文件名
        return local_file.name


def build_remote_path(remote_base, relative_path):
    """
    构建远端完整路径
    
    Args:
        remote_base: 远端基础目录
        relative_path: 相对路径（使用 / 分隔）
        
    Returns:
        str: 远端完整路径
    """
    # 确保远端基础目录以 / 开头
    if not remote_base.startswith('/'):
        remote_base = '/' + remote_base
    
    # 移除相对路径开头的 ./
    relative_path = relative_path.lstrip('./')
    
    # 组合路径
    if relative_path:
        # 将 Windows 路径分隔符转换为 /
        relative_path = relative_path.replace('\\', '/')
        remote_path = f"{remote_base.rstrip('/')}/{relative_path}"
    else:
        remote_path = remote_base
    
    return remote_path


def create_upload_tasks(local_files, subdirs, remote_dir, local_base_dir=None):
    """
    创建上传任务列表
    
    Args:
        local_files: 本地文件路径列表
        subdirs: 远端子文件夹列表（如果为None或空，上传到根目录）
        remote_dir: 远端根目录
        local_base_dir: 本地基础目录（用于保持目录结构，可选）
        
    Returns:
        list: 任务列表，每个元素为 {'local_file': 本地文件, 'remote_dir': 远端目录, 'remote_path': 远端完整路径, 'file_name': 文件名}
    """
    tasks = []
    
    if subdirs:
        # 如果有子文件夹，将每个文件复制到所有子文件夹
        for local_file in local_files:
            file_name = os.path.basename(local_file)
            for target_subdir in subdirs:
                remote_path = f"{target_subdir}/{file_name}"
                tasks.append({
                    'local_file': local_file,
                    'remote_dir': target_subdir,
                    'remote_path': remote_path,
                    'file_name': file_name
                })
    else:
        # 没有子文件夹，上传到根目录
        for local_file in local_files:
            if local_base_dir:
                # 保持目录结构
                relative_path = get_relative_path(local_file, local_base_dir)
                remote_path = build_remote_path(remote_dir, relative_path)
                remote_file_dir = '/'.join(remote_path.split('/')[:-1])
            else:
                # 简化处理：只上传文件名
                file_name = os.path.basename(local_file)
                remote_path = build_remote_path(remote_dir, file_name)
                remote_file_dir = remote_dir
            
            tasks.append({
                'local_file': local_file,
                'remote_dir': remote_file_dir,
                'remote_path': remote_path,
                'file_name': os.path.basename(local_file)
            })
    
    return tasks


def save_tasks_status(tasks, status_file='upload_tasks_status.json'):
    """
    保存任务状态到文件
    
    Args:
        tasks: 任务列表（包含状态信息）
        status_file: 状态文件路径
    """
    try:
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"警告：保存任务状态失败: {e}")


def load_tasks_status(status_file='upload_tasks_status.json'):
    """
    从文件加载任务状态
    
    Args:
        status_file: 状态文件路径
        
    Returns:
        dict: 任务状态字典，key为任务ID，value为状态
    """
    if not os.path.exists(status_file):
        return {}
    
    try:
        with open(status_file, 'r', encoding='utf-8') as f:
            saved_tasks = json.load(f)
        
        # 转换为字典，key为任务ID（基于本地路径和远端路径）
        status_dict = {}
        for task in saved_tasks:
            task_id = f"{task.get('local_file', '')}|{task.get('remote_path', '')}"
            status_dict[task_id] = task.get('status', 'pending')
        
        return status_dict
    except Exception as e:
        print(f"警告：加载任务状态失败: {e}")
        return {}


def get_task_id(task):
    """生成任务唯一ID"""
    import hashlib
    # 使用本地文件和远端路径生成唯一ID
    task_str = f"{task.get('local_file', '')}|{task.get('remote_path', '')}"
    return hashlib.md5(task_str.encode('utf-8')).hexdigest()[:8]


def get_status_file_path(local_path, remote_dir):
    """
    根据本地路径和远端目录生成唯一的状态文件名
    文件保存在 upload_tasks_status/ 文件夹中，使用有规律的命名
    
    Args:
        local_path: 本地路径（文件或目录）
        remote_dir: 远端目录
        
    Returns:
        str: 状态文件路径
    """
    import hashlib
    import re
    from pathlib import Path
    
    # 创建状态文件目录
    status_dir = Path('upload_tasks_status')
    status_dir.mkdir(exist_ok=True)
    
    # 获取本地路径的简化名称（文件名或目录名）
    local_path_obj = Path(local_path)
    if local_path_obj.is_file():
        local_name = local_path_obj.stem  # 文件名（不含扩展名）
    else:
        local_name = local_path_obj.name  # 目录名
    
    # 清理名称，移除特殊字符，只保留字母、数字、下划线和连字符
    local_name_clean = re.sub(r'[^\w\-]', '_', local_name)
    
    # 获取远端目录的简化名称（最后一级目录名）
    remote_name = Path(remote_dir).name if remote_dir else 'root'
    remote_name_clean = re.sub(r'[^\w\-]', '_', remote_name)
    
    # 使用本地路径和远端目录生成唯一ID（用于区分相同名称的不同路径）
    unique_str = f"{str(local_path)}|{remote_dir}"
    file_hash = hashlib.md5(unique_str.encode('utf-8')).hexdigest()[:8]
    
    # 生成文件名：日期_本地名称_远端名称_哈希.json
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{date_str}_{local_name_clean}_{remote_name_clean}_{file_hash}.json"
    
    return str(status_dir / filename)


def execute_upload_tasks(cmd, tasks, overwrite=True, resume=False, status_file='upload_tasks_status.json'):
    """
    执行上传任务列表，支持断点续传
    
    Args:
        cmd: BaiduPCS-Go 命令
        tasks: 任务列表
        overwrite: 是否覆盖同名文件
        resume: 是否启用断点续传
        status_file: 任务状态文件路径
        
    Returns:
        list: 上传结果列表
    """
    results = []
    total_tasks = len(tasks)
    
    # 如果启用断点续传，加载之前的任务状态
    saved_status = {}
    if resume:
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    saved_tasks_list = json.load(f)
                # 转换为字典，key为任务ID
                for saved_task in saved_tasks_list:
                    task_id = get_task_id(saved_task)
                    saved_status[task_id] = saved_task.get('status', 'pending')
                if saved_status:
                    print(f"📋 检测到任务状态文件: {status_file}")
                    print(f"   已加载 {len(saved_status)} 个任务状态\n")
            except Exception as e:
                print(f"⚠️  加载任务状态失败: {e}，将重新开始\n")
        else:
            print(f"ℹ️  未找到任务状态文件: {status_file}，将从头开始\n")
    
    # 为每个任务添加状态和任务ID
    for task in tasks:
        task['task_id'] = get_task_id(task)
        if resume and task['task_id'] in saved_status:
            task['status'] = saved_status[task['task_id']]
        else:
            task['status'] = 'pending'
    
    # 统计任务状态
    pending_count = sum(1 for t in tasks if t['status'] == 'pending')
    success_count = sum(1 for t in tasks if t['status'] == 'success')
    failed_count = sum(1 for t in tasks if t['status'] == 'failed')
    
    print(f"\n{'='*60}")
    print(f"开始执行上传任务")
    print(f"{'='*60}")
    print(f"总共 {total_tasks} 个任务")
    if resume:
        print(f"  待执行: {pending_count} 个")
        print(f"  已成功: {success_count} 个")
        print(f"  已失败: {failed_count} 个（将重试）")
    print()
    
    # 执行任务
    executed_count = 0
    for idx, task in enumerate(tasks, 1):
        local_file = task['local_file']
        remote_dir = task['remote_dir']
        remote_path = task['remote_path']
        file_name = task['file_name']
        task_status = task['status']
        
        # 如果任务已成功且启用断点续传，跳过
        if task_status == 'success' and resume:
            print(f"[{idx}/{total_tasks}] 跳过（已成功）: {file_name} -> {remote_path}")
            results.append({
                'local_path': local_file,
                'remote_path': remote_path,
                'success': True,
                'error': None,
                'skipped': True
            })
            continue
        
        executed_count += 1
        print(f"[{idx}/{total_tasks}] 上传: {file_name}")
        print(f"  本地: {local_file}")
        print(f"  远端: {remote_path}")
        print(f"  目录: {os.path.basename(remote_dir)}")
        if task_status == 'failed':
            print(f"  状态: 重试（之前失败）")
        
        success, error = upload_file(cmd, local_file, remote_dir, overwrite)
        
        # 更新任务状态
        if success:
            task['status'] = 'success'
            print("  ✅ 成功\n")
        else:
            task['status'] = 'failed'
            print(f"  ❌ 失败: {error}\n")
        
        results.append({
            'local_path': local_file,
            'remote_path': remote_path,
            'success': success,
            'error': error
        })
        
        # 定期保存任务状态（每10个任务或最后一个任务）
        if executed_count % 10 == 0 or idx == total_tasks:
            save_tasks_status(tasks, status_file)
    
    # 最后保存一次任务状态
    save_tasks_status(tasks, status_file)
    
    # 注意：失败处理由主函数负责，这里只返回结果
    return results


def upload_directory(cmd, local_dir, remote_dir, overwrite=True, resume=False, status_file=None):
    """
    递归上传整个目录
    如果远端目录包含子文件夹，会将文件上传到这些子文件夹中
    
    Args:
        cmd: BaiduPCS-Go 命令
        local_dir: 本地目录路径
        remote_dir: 远端目标目录
        overwrite: 是否覆盖同名文件
        resume: 是否启用断点续传
        status_file: 任务状态文件路径（如果为None，会自动生成）
        
    Returns:
        list: 上传结果列表，每个元素为 (本地路径, 远端路径, 是否成功, 错误信息)
    """
    local_dir = Path(local_dir).resolve()
    
    # 先递归查询远端目录结构，获取所有子文件夹
    print(f"\n{'='*60}")
    print(f"正在递归查询远端目录结构: {remote_dir}")
    print(f"{'='*60}")
    subdirs = get_remote_subdirectories(cmd, remote_dir, recursive=True)
    
    if subdirs:
        print(f"\n✅ 发现 {len(subdirs)} 个子文件夹:")
        for i, subdir in enumerate(subdirs, 1):
            print(f"  {i}. {subdir}")
        print(f"\n将使用这些子文件夹进行文件分配...\n")
    else:
        print("\n⚠️  未发现子文件夹，将上传到根目录\n")
    
    # 收集所有要上传的文件
    files_to_upload = []
    for root, dirs, files in os.walk(local_dir):
        for file in files:
            local_file = os.path.join(root, file)
            files_to_upload.append(str(local_file))
    
    print(f"📁 本地文件夹包含 {len(files_to_upload)} 个文件\n")
    
    # 创建上传任务列表
    print(f"{'='*60}")
    print(f"创建上传任务")
    print(f"{'='*60}")
    tasks = create_upload_tasks(files_to_upload, subdirs, remote_dir, local_base_dir=str(local_dir))
    
    print(f"✅ 已创建 {len(tasks)} 个上传任务:")
    for idx, task in enumerate(tasks, 1):
        print(f"  {idx}. {task['file_name']} -> {task['remote_path']}")
    print()
    
    # 执行上传任务
    if status_file is None:
        status_file = get_status_file_path(local_dir, remote_dir)
    results = execute_upload_tasks(cmd, tasks, overwrite, resume=resume, status_file=status_file)
    
    return results


def save_upload_log(results, log_dir='upload_logs'):
    """
    保存上传记录到日志文件
    
    Args:
        results: 上传结果列表
        log_dir: 日志目录
    """
    # 创建日志目录
    os.makedirs(log_dir, exist_ok=True)
    
    # 按日期创建日志文件
    today = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'upload_log_{today}.json')
    
    # 读取现有日志（如果存在）
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            existing_logs = json.load(f)
    else:
        existing_logs = []
    
    # 添加新记录
    for result in results:
        if result['success']:
            log_entry = {
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'local_path': result['local_path'],
                'remote_path': result['remote_path'],
                'file_size': os.path.getsize(result['local_path']) if os.path.exists(result['local_path']) else 0,
                'status': 'success'
            }
            existing_logs.append(log_entry)
        else:
            # 也记录失败的文件
            log_entry = {
                'upload_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'local_path': result['local_path'],
                'remote_path': result['remote_path'],
                'status': 'failed',
                'error': result['error']
            }
            existing_logs.append(log_entry)
    
    # 保存日志
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, ensure_ascii=False, indent=2)
    
    print(f"\n上传记录已保存到: {log_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='上传文件或文件夹到百度网盘',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用参数方式（推荐）
  python upload.py --local-file /path/to/file.txt --remote-dir /我的文件/备份
  python upload.py --local-file /path/to/folder --remote-dir /我的文件/备份
  
  # 使用位置参数方式（向后兼容）
  python upload.py /path/to/file.txt /我的文件/备份
  python upload.py /path/to/folder /我的文件/备份
  
  # 断点续传（从上次失败的地方继续）
  python upload.py --local-file /path/to/file.txt --remote-dir /我的文件/备份 --resume
  
  # 清除任务状态，重新开始
  python upload.py --local-file /path/to/file.txt --remote-dir /我的文件/备份 --clear-status
        """
    )
    
    # 使用参数方式（推荐）
    parser.add_argument('--local-file', '--local-path', dest='local_path',
                       help='本地文件或文件夹路径（可以是文件或文件夹）')
    parser.add_argument('--remote-dir', '--remote-path', dest='remote_dir',
                       help='远端目标目录路径（如: /我的文件/备份）')
    
    # 位置参数（向后兼容）
    parser.add_argument('local_path_pos', nargs='?',
                       help='本地文件或文件夹路径（位置参数，向后兼容）')
    parser.add_argument('remote_dir_pos', nargs='?',
                       help='远端目标目录路径（位置参数，向后兼容）')
    
    parser.add_argument('--overwrite', action='store_true', default=True,
                       help='覆盖同名文件（默认: True）')
    parser.add_argument('--resume', action='store_true',
                       help='启用断点续传，从上次失败的地方继续')
    parser.add_argument('--clear-status', action='store_true',
                       help='清除任务状态文件，重新开始')
    
    args = parser.parse_args()
    
    # 确定使用哪个参数（优先使用 --local-dir 和 --remote-dir）
    local_path = args.local_path or args.local_path_pos
    remote_dir = args.remote_dir or args.remote_dir_pos
    
    # 检查必需参数
    if not local_path:
        parser.error("必须指定本地路径（使用 --local-file 或位置参数）")
    if not remote_dir:
        parser.error("必须指定远端目录（使用 --remote-dir 或位置参数）")
    
    # 检查 BaiduPCS-Go
    baidupcs_cmd = check_baidupcs_go()
    if not baidupcs_cmd:
        print("错误：未找到 BaiduPCS-Go 命令！")
        print("请先安装 BaiduPCS-Go 并确保它在系统 PATH 中")
        sys.exit(1)
    
    print(f"使用 BaiduPCS-Go: {baidupcs_cmd}\n")
    
    # 检查本地路径
    local_path = Path(local_path).resolve()
    if not local_path.exists():
        print(f"错误：本地路径不存在: {local_path}")
        sys.exit(1)
    
    # 检查远端目录是否存在
    print(f"检查远端目录: {remote_dir}")
    if not check_remote_directory_exists(baidupcs_cmd, remote_dir):
        print(f"\n❌ 错误：远端目录不存在: {remote_dir}")
        print("请先创建该目录或检查路径是否正确")
        sys.exit(1)
    
    print("✅ 远端目录存在\n")
    
    # 开始上传
    results = []
    
    # 先查询远端目录结构，看是否有子文件夹
    print(f"\n{'='*60}")
    print(f"正在递归查询远端目录结构: {remote_dir}")
    print(f"{'='*60}")
    subdirs = get_remote_subdirectories(baidupcs_cmd, remote_dir, recursive=True)
    
    if subdirs:
        print(f"\n✅ 发现 {len(subdirs)} 个子文件夹:")
        for i, subdir in enumerate(subdirs, 1):
            print(f"  {i}. {subdir}")
        print(f"\n将使用这些子文件夹进行文件分配...\n")
    else:
        print("\n⚠️  未发现子文件夹，将上传到根目录\n")
    
    if local_path.is_file():
        # 上传单个文件 - 使用与文件夹上传相同的逻辑
        print(f"上传文件: {local_path}")
        print(f"目标目录: {remote_dir}\n")
        
        # 收集文件（单个文件也作为列表处理，保持逻辑一致）
        files_to_upload = [str(local_path)]
        
        print(f"📁 准备上传 {len(files_to_upload)} 个文件\n")
        
        # 创建上传任务列表
        print(f"{'='*60}")
        print(f"创建上传任务")
        print(f"{'='*60}")
        tasks = create_upload_tasks(files_to_upload, subdirs, remote_dir)
        
        print(f"✅ 已创建 {len(tasks)} 个上传任务:")
        for idx, task in enumerate(tasks, 1):
            print(f"  {idx}. {task['file_name']} -> {task['remote_path']}")
        print()
        
        # 生成唯一的状态文件名（基于本地路径和远端目录）
        status_file = get_status_file_path(local_path, remote_dir)
        
        # 清除状态文件（如果指定）
        if args.clear_status:
            if os.path.exists(status_file):
                os.remove(status_file)
                print("✅ 已清除任务状态文件\n")
            else:
                print("ℹ️  未找到任务状态文件\n")
        
        # 执行上传任务
        results = execute_upload_tasks(baidupcs_cmd, tasks, args.overwrite, 
                                      resume=args.resume, status_file=status_file)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get('success', False))
        skipped_count = sum(1 for r in results if r.get('skipped', False))
        fail_count = len(results) - success_count - skipped_count
        
        print(f"\n{'='*60}")
        print(f"上传完成")
        print(f"{'='*60}")
        print(f"成功: {success_count} 个文件")
        if skipped_count > 0:
            print(f"跳过: {skipped_count} 个文件（已成功）")
        print(f"失败: {fail_count} 个文件")
        
        if fail_count > 0:
            print(f"\n{'='*60}")
            print(f"⚠️  有 {fail_count} 个文件上传失败")
            print(f"{'='*60}\n")
            print("失败的文件:")
            for idx, r in enumerate(results, 1):
                if not r.get('success', False) and not r.get('skipped', False):
                    print(f"  {idx}. {r.get('local_path', '未知')}")
                    print(f"     -> {r.get('remote_path', '未知')}")
                    if r.get('error'):
                        print(f"     错误: {r['error']}")
            
            # 获取状态文件路径
            status_file = get_status_file_path(local_path, remote_dir)
            print(f"\n任务状态已保存到: {status_file}")
            print(f"\n💡 提示：使用以下命令从失败的地方继续上传：")
            print(f"   python upload.py --local-file \"{local_path}\" --remote-dir \"{remote_dir}\" --resume")
            print()
            sys.exit(1)
            
    elif local_path.is_dir():
        # 上传整个目录
        print(f"上传目录: {local_path}")
        print(f"目标目录: {remote_dir}\n")
        print("开始递归上传...\n")
        
        # 生成唯一的状态文件名
        status_file = get_status_file_path(local_path, remote_dir)
        
        # 清除状态文件（如果指定）
        if args.clear_status:
            if os.path.exists(status_file):
                os.remove(status_file)
                print("✅ 已清除任务状态文件\n")
            else:
                print("ℹ️  未找到任务状态文件\n")
        
        results = upload_directory(baidupcs_cmd, str(local_path), remote_dir, 
                                   args.overwrite, resume=args.resume, status_file=status_file)
        
        # 统计结果
        success_count = sum(1 for r in results if r.get('success', False))
        skipped_count = sum(1 for r in results if r.get('skipped', False))
        fail_count = len(results) - success_count - skipped_count
        
        print(f"\n{'='*60}")
        print(f"上传完成")
        print(f"{'='*60}")
        print(f"成功: {success_count} 个文件")
        if skipped_count > 0:
            print(f"跳过: {skipped_count} 个文件（已成功）")
        print(f"失败: {fail_count} 个文件")
        
        if fail_count > 0:
            print(f"\n{'='*60}")
            print(f"⚠️  有 {fail_count} 个文件上传失败")
            print(f"{'='*60}\n")
            print("失败的文件:")
            for idx, r in enumerate(results, 1):
                if not r.get('success', False) and not r.get('skipped', False):
                    print(f"  {idx}. {r.get('local_path', '未知')}")
                    print(f"     -> {r.get('remote_path', '未知')}")
                    if r.get('error'):
                        print(f"     错误: {r['error']}")
            
            # 获取状态文件路径
            status_file = get_status_file_path(local_path, remote_dir)
            print(f"\n任务状态已保存到: {status_file}")
            print(f"\n💡 提示：使用以下命令从失败的地方继续上传：")
            print(f"   python upload.py --local-file \"{local_path}\" --remote-dir \"{remote_dir}\" --resume")
            print()
            sys.exit(1)
    else:
        print(f"错误：路径既不是文件也不是目录: {local_path}")
        sys.exit(1)
    
    # 保存上传记录
    if results:
        save_upload_log(results)


if __name__ == '__main__':
    main()
