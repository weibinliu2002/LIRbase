import gzip
import pandas as pd
import json
import rpy2.robjects as ro
from Bio import SeqIO


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
    try:
        ro.r['load'](path)  # 使用 rpy2 加载 RData 文件
        summary = ro.r['summary']  # 获取 summary 对象
        return summary
    except Exception as e:
        return str(e)