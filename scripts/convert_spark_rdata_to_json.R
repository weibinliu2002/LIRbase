library(jsonlite)

convert_one_spark <- function(infile, outfile) {
  rm(list = ls())

  e <- new.env()
  load(infile, envir = e)

  # 检查文件是否有 summary 对象
  if (!exists("summary", envir = e)) {
    cat("跳过：", infile, "，没有 summary 对象\n")
    return(NULL)
  }

  summary_data <- get("summary", envir = e)

  # 转换为 list
  out <- list(
    spark_summary = as.list(summary_data)
  )

  # 创建输出目录
  dir.create(dirname(outfile), recursive = TRUE, showWarnings = FALSE)
  
  # 写入 JSON 文件
  write_json(out, outfile, auto_unbox = TRUE, pretty = TRUE)

  cat("已转换：", infile, "->", outfile, "\n")
}

input_dir <- "www/Spark_data"  # 旧网站的文件路径
output_dir <- "data/Spark_json"  # 新的 Spark 数据 JSON 存放目录

# 获取所有 .RData 文件
files <- list.files(
  input_dir,
  pattern = "\\.RData$",
  recursive = TRUE,
  full.names = TRUE
)

# 批量转换 RData 为 JSON
for (f in files) {
  # 生成相对路径，替换后缀为 .json
  rel_path <- sub(paste0("^", input_dir, "/?"), "", f)
  out_file <- file.path(
    output_dir,
    sub("\\.RData$", ".spark.json", rel_path)
  )
  convert_one_spark(f, out_file)
}