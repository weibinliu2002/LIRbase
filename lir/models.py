from django.db import models


class Species(models.Model):
    accession = models.CharField(max_length=200, unique=True)
    species = models.CharField(max_length=200, blank=True)
    division = models.CharField(max_length=50, blank=True)   # Diploidy / Tetraploidy / Other
    ploidy = models.CharField(max_length=50, blank=True)
    blast_db = models.CharField(max_length=255, blank=True)
    number_of_lir = models.IntegerField(null=True, blank=True)
    genome_length = models.CharField(max_length=100, blank=True)

    table_file = models.CharField(max_length=500, blank=True)
    fasta_file = models.CharField(max_length=500, blank=True)
    irf_json_file = models.CharField(max_length=500, blank=True)
    spark_json_file = models.CharField(max_length=500, blank=True)
    gene_overlap_file = models.CharField(max_length=500, blank=True)

    def __str__(self):
        return self.accession

class ChromSize(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="chrom_sizes")
    chrom = models.CharField(max_length=100)
    size = models.BigIntegerField()
    division = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = ("species", "chrom")

    def __str__(self):
        return f"{self.species.accession} - {self.chrom}"