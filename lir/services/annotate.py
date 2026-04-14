import os
import re
import subprocess
import tempfile
import logging


logger = logging.getLogger(__name__)


def normalize_fasta_input(seq_text: str) -> str:
    seq_text = seq_text.strip()
    if not seq_text:
        raise ValueError("请输入 FASTA 序列或上传 FASTA 文件")

    if not seq_text.startswith(">"):
        seq_text = ">query\n" + seq_text

    lines = [x.strip() for x in seq_text.splitlines() if x.strip()]
    return "\n".join(lines) + "\n"


def read_fasta_dict(fasta_path: str):
    seqs = {}
    name = None
    chunks = []

    with open(fasta_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if name is not None:
                    seqs[name] = "".join(chunks)
                name = line[1:].strip().split()[0]
                chunks = []
            else:
                chunks.append(line)
        if name is not None:
            seqs[name] = "".join(chunks)

    return seqs


def parse_irf_dat_like_r(dat_file: str):
    with open(dat_file, "r", encoding="utf-8", errors="ignore") as f:
        dat = [x.rstrip("\n") for x in f]

    if len(dat) <= 8:
        return []

    # 对齐 R: dat <- dat[-c(1:8)]
    dat = dat[8:]

    seq_idx = [i for i, x in enumerate(dat) if re.search(r"^Sequence:", x)]
    if not seq_idx:
        return []

    seq_idx.append(len(dat))
    collected = []

    for i in range(len(seq_idx) - 1):
        start = seq_idx[i]
        end = seq_idx[i + 1]

        seq_line = dat[start]
        seq_id = re.sub(r"^Sequence:\s*", "", seq_line).strip()

        block = dat[start:end]
        block = [x for x in block if re.search(r"^\d", x)]

        for line in block:
            parts = re.split(r"\s+", line.strip())
            if len(parts) >= 11:
                row = [seq_id] + parts[:11]
                collected.append(row)

    rows = []
    for row in collected:
        try:
            chr_name = row[0]
            left_start = int(row[1])
            left_end = int(row[2])
            left_len = int(row[3])
            right_start = int(row[4])
            right_end = int(row[5])
            right_len = int(row[6])
            loop_len = int(row[7])
            match_per = float(row[8])
            indel_per = float(row[9])
            score = int(float(row[10]))

            lir_id = f"{chr_name}:{left_start}--{left_end},{right_start}--{right_end}"

            rows.append({
                "ID": lir_id,
                "chr": chr_name,
                "Left_start": left_start,
                "Left_end": left_end,
                "Left_len": left_len,
                "Right_start": right_start,
                "Right_end": right_end,
                "Right_len": right_len,
                "Loop_len": loop_len,
                "Match_per": match_per,
                "Indel_per": indel_per,
                "Score": score,
            })
        except Exception:
            continue

    return rows


def parse_irf_html_alignments(tmpdir: str, fasta_basename: str):
    align_dict = {}

    html_files = []
    for fname in os.listdir(tmpdir):
        if fname.startswith(fasta_basename) and fname.endswith(".txt.html"):
            html_files.append(os.path.join(tmpdir, fname))

    for html_file in html_files:
        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            d = [x.rstrip("\n") for x in f]

        x_name = [i for i, line in enumerate(d) if "NAME=" in line]
        x_stat = [i for i, line in enumerate(d) if "Statistics" in line]

        if len(d) >= 10:
            chr_id = d[9].replace("Sequence: ", "").strip()
        else:
            chr_id = "query"

        for i in range(min(len(x_name), len(x_stat))):
            start = x_name[i] + 5
            end = x_stat[i] - 4
            block = d[start:end] if start < end else []

            if x_name[i] + 1 < len(d):
                name_line = d[x_name[i] + 1]
                name_line = re.sub(r"\s+Loop:.+", "", name_line)
                name_line = re.sub(r".+\s", "", name_line)
                lir_id = f"{chr_id}:{name_line}"
                align_dict[lir_id] = block

    return align_dict


def build_annotated_fasta_rows(table_rows, fasta_dict, flank_len=200):
    fasta_result = {}

    for r in table_rows:
        chr_name = r["chr"]
        if chr_name not in fasta_dict:
            continue

        seq = fasta_dict[chr_name]
        chr_len = len(seq)

        left_start = r["Left_start"]
        left_end = r["Left_end"]
        right_start = r["Right_start"]
        right_end = r["Right_end"]

        loop_start = left_end + 1
        loop_end = right_start - 1

        left_start_n = max(1, left_start - flank_len)
        right_end_n = min(chr_len, right_end + flank_len)

        lf = seq[left_start_n - 1:left_start - 1].lower()
        larm = seq[left_start - 1:left_end].upper()
        loop = seq[loop_start - 1:loop_end].lower() if loop_start <= loop_end else ""
        rarm = seq[right_start - 1:right_end].upper()
        rf = seq[right_end:right_end_n].lower()

        full_seq = lf + larm + loop + rarm + rf
        fasta_result[r["ID"]] = full_seq

    return fasta_result


def run_irf(
    fasta_text: str,
    irf_executable: str,
    match: int = 2,
    mismatch: int = 3,
    delta: int = 5,
    pm: int = 80,
    pi: int = 10,
    minscore: int = 40,
    maxlength: int = 100000,
    maxloop: int = 50000,
    flanklen: int = 200,
    min_arm_len: int = 400,
):
    # 确保 irf_executable 是字符串
    irf_executable = str(irf_executable)
    fasta_text = normalize_fasta_input(fasta_text)

    if not os.path.exists(irf_executable):
        raise RuntimeError(f"IRF 可执行文件不存在: {irf_executable}")

    if not os.access(irf_executable, os.X_OK):
        raise RuntimeError(f"IRF 文件没有执行权限: {irf_executable}")

    with tempfile.TemporaryDirectory() as tmpdir:
        fasta_name = "input.fa"
        fasta_file = os.path.join(tmpdir, fasta_name)
        #logger.info(fasta_text)
        logger.info(f"写入 IRF 输入文件: {fasta_file}")
        
        try:
            with open(fasta_file, "w", encoding="utf-8") as f:
                f.write(fasta_text)
            #logger.info("文件写入成功")
            #logger.info(f"文件大小: {os.path.getsize(fasta_file)} 字节")
        except Exception as e:
            logger.error(f"文件写入失败: {e}")
            raise

        # 对齐 R:
        # irf305.linux.exe input.fa match mismatch delta pm pi minscore maxlength maxloop -d -f flanklen
        cmd = [
            irf_executable,
            fasta_name,
            str(match),
            str(mismatch),
            str(delta),
            str(pm),
            str(pi),
            str(minscore),
            str(maxlength),
            str(maxloop),
            "-d",
            "-f",
            str(flanklen),
        ]

        result = subprocess.run(
            cmd,
            cwd=tmpdir,
            capture_output=True,
            text=True
        )

        tmp_files = sorted(os.listdir(tmpdir))
        logger.info(f"临时目录文件: {tmp_files}")
        
        dat_candidates = [f for f in tmp_files if f.endswith(".dat")]
        html_candidates = [f for f in tmp_files if f.endswith(".html")]
        
        #logger.info(f"dat 文件候选: {dat_candidates}")
        #logger.info(f"html 文件候选: {html_candidates}")
        
        # IRF 3.09 可能把正常日志写到 stderr，不能仅凭 stderr 或 returncode 判断失败
        # 只要生成了结果文件，就继续解析
        if not dat_candidates and not html_candidates:
            raise RuntimeError(
                "IRF 没有生成任何结果文件\n"
                f"returncode: {result.returncode}\n"
                f"命令: {' '.join(cmd)}\n"
                f"临时目录文件: {tmp_files}\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )

        dat_file = None
        if dat_candidates:
            dat_file = os.path.join(tmpdir, dat_candidates[0])
            logger.info(f"dat 文件: {dat_file}")
        '''with open(dat_file, "r", encoding="utf-8") as f:
            dat_content = f.read()
        logger.info(f"dat 文件内容: {dat_content}")
        dat_content = dat_content.strip()'''
        # 有些版本可能只生成 html，不生成 dat；这种情况不直接报 IRF 失败，而是返回空表+调试信息
        if not dat_file or not os.path.exists(dat_file):
            return {
                "table_all": [],
                "table": [],
                "fasta": {},
                "align": parse_irf_html_alignments(tmpdir, fasta_name),
                "log": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "tmp_files": tmp_files,
                "cmd": " ".join(cmd),
                "returncode": result.returncode,
                "warning": "IRF 已运行，但没有找到 .dat 文件；请检查该版本输出格式。",
            }
        
        
        raw_rows = parse_irf_dat_like_r(dat_file)
        #logger.info(f"解析: {raw_rows}")
        
        filtered_rows = [
            r for r in raw_rows
            if r["Left_len"] >= min_arm_len
            and r["Right_len"] >= min_arm_len
            and r["Loop_len"] <= maxloop
        ]
        #logger.info(f"过滤: {filtered_rows}")
        
        fasta_dict = read_fasta_dict(fasta_file)
        #logger.info(f"fasta_dict: {fasta_dict}")

        fasta_rows = build_annotated_fasta_rows(filtered_rows, fasta_dict, flank_len=int(flanklen))
        #logger.info(f"fasta_rows: {fasta_rows}")
        align_rows = parse_irf_html_alignments(tmpdir, fasta_name)
        #logger.info(f"align_rows: {align_rows}")

        return {
            "table_all": raw_rows,
            "table": filtered_rows,
            "fasta": fasta_rows,
            "align": align_rows,
            "log": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "tmp_files": tmp_files,
            "cmd": " ".join(cmd),
            "returncode": result.returncode,
            "warning": "",
        }
