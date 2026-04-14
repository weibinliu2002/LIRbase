library(jsonlite)

convert_one_irf <- function(infile, outfile) {
  e <- new.env()
  load(infile, envir = e)
  
  if (!exists("LIR.align", envir = e)) {
    cat("跳过：", infile, "，因为没有对象 LIR.align\n")
    return(NULL)
  }
  
  lir_align <- get("LIR.align", envir = e)
  # 确保每个 ID 都保留格式
  out_align <- lapply(lir_align, function(x) {
    # 如果每个元素本身就有换行符，直接返回
    paste(x, collapse = "\n")
  })
  
  # 创建最终的 JSON 结构
  out <- list(
    LIR_align = out_align
  )
  
  dir.create(dirname(outfile), recursive = TRUE, showWarnings = FALSE)
  write_json(out, outfile, auto_unbox = TRUE, pretty = TRUE)
  
  cat("已转换：", infile, "->", outfile, "\n")
}

# 使用路径并调用转换函数
input_dir <- "D://桌面/毕业课题/代码/LIRBase-main/www/HTML/Diploidy/"
output_dir <- "D://桌面/毕业课题/代码/LIRBase-main/www/HTML/Diploidy/"

files <- list.files(
  input_dir,
  pattern = "\\.IRFresult\\.RData$",
  recursive = TRUE,
  full.names = TRUE
)

for (f in files) {
  rel_path <- sub(paste0("^", input_dir, "/?"), "", f)
  out_file <- file.path(
    output_dir,
    sub("\\.IRFresult\\.RData$", ".irf.json", rel_path)
  )
  convert_one_irf(f, out_file)
}
for (line in lir_align) {
  print(line)
}

