import csv
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from lir.models import Species, ChromSize

csv_file = "data/metadata/chrom_sizes.csv"

with open(csv_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        accession = row["ID"].strip()
        chrom = row["chr"].strip()
        size = int(row["size"])
        division = row.get("Division", "").strip()

        try:
            sp = Species.objects.get(accession=accession)
        except Species.DoesNotExist:
            print(f"跳过：Species 不存在 -> {accession}")
            continue

        ChromSize.objects.update_or_create(
            species=sp,
            chrom=chrom,
            defaults={
                "size": size,
                "division": division,
            }
        )

print("ChromSize 导入完成")
