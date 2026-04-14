import csv
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from lir.models import Species

csv_file = "data/metadata/species_index.csv"

with open(csv_file, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        Species.objects.update_or_create(
            accession=row["accession"],
            defaults={
                "species": row["species"],
                "division": row["division"],
                "ploidy": row["ploidy"],
                "number_of_lir": int(row["number_of_lir"]) if row["number_of_lir"] else None,
                "genome_length": row["genome_length"],
                "table_file": row["table_file"],
                "fasta_file": row["fasta_file"],
                "irf_json_file": row["irf_json_file"],
                "spark_json_file": row["spark_json_file"],
                "gene_overlap_file": row["gene_overlap_file"],
            }
        )

print("Species 导入完成")
