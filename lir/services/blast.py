import os
import subprocess
import tempfile
from django.conf import settings

def normalize_fasta_input(seq_text: str) -> str:
    seq_text = seq_text.strip()
    if not seq_text:
        raise ValueError("请输入序列或上传 FASTA 文件")

    # 如果用户没有写 fasta 头，就自动补一个
    if not seq_text.startswith(">"):
        seq_text = ">query\n" + seq_text

    return seq_text


def run_blastn(query_text: str, db_path: str, evalue: str = "10", max_hits: str = "10"):
    query_text = normalize_fasta_input(query_text)

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".fa") as qf:
        qf.write(query_text)
        query_file = qf.name

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt") as of:
        out_file = of.name
        
    try:
        cmd = [
            settings.BLASTN_EXECUTABLE,
            "-query", query_file,
            "-db", db_path,
            "-evalue", str(evalue),
            "-max_target_seqs", str(max_hits),
            "-outfmt", "6 qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore",
            "-out", out_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "blastn 运行失败")

        rows = []
        with open(out_file, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) != 12:
                    continue

                rows.append({
                    "qseqid": parts[0],
                    "sseqid": parts[1],
                    "pident": parts[2],
                    "length": parts[3],
                    "mismatch": parts[4],
                    "gapopen": parts[5],
                    "qstart": parts[6],
                    "qend": parts[7],
                    "sstart": parts[8],
                    "send": parts[9],
                    "evalue": parts[10],
                    "bitscore": parts[11],
                })

        return rows

    finally:
        if os.path.exists(query_file):
            os.remove(query_file)
        if os.path.exists(out_file):
            os.remove(out_file)