import os
import gzip
import platform

import pandas as pd
import json
from Bio import SeqIO

# 尝试导入 rpy2.robjects
ro = None
try:
    # 设置 R_HOME 环境变量

    system = platform.system().lower()
    if system == 'windows':
        os.environ['R_HOME'] = r'D:\software\R\R-4.5.2'
    elif system == 'linux':
        os.environ['R_HOME'] = r'/usr/bin/R'
    else:
        os.environ['R_HOME'] = r'/usr/lib/R-4.5.2'
    
    # 将 R 的 bin 目录添加到 PATH 环境变量
    r_bin_dir = os.path.join(os.environ['R_HOME'], 'bin', 'x64')
    os.environ['PATH'] = r_bin_dir + ';' + os.environ['PATH']
    
    import rpy2.robjects as ro
except Exception as e:
    print(f"Warning: Failed to import rpy2.robjects: {e}")
    ro = None

def load_lir_table(path):
    """
    读取某个物种的 LIR 主表 .dat.gz
    """
    df = pd.read_csv(path, sep="\t", compression="gzip")
    return df

def load_gene_overlap(path):
    """
    读取某个物种的 LIR 与基因 overlap 表
    """
    df = pd.read_csv(path, sep="\t", compression="gzip")
    return df

def load_fasta_as_dict(path):
    """
    读取 fasta.gz，返回 {record_id: sequence} 字典
    """
    fasta_dict = {}
    with gzip.open(path, "rt") as handle:
        for record in SeqIO.parse(handle, "fasta"):
            fasta_dict[record.id] = str(record.seq)
    return fasta_dict
def load_irf_json(path):
    """
    读取 IRF JSON
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
def load_spark_summary(path):
    """
    读取 Spark summary RData
    """
    if ro is None:
        return "Error: rpy2.robjects not available"
    try:
        ro.r['load'](path)  # 使用 rpy2 加载 RData 文件
        summary = ro.r['summary']  # 获取 summary 对象
        return summary
    except Exception as e:
        return str(e)