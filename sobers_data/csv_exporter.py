import csv
import os

from .models import get_transformer, BankDataLineTransformer


class CSVBankDataExporter:
    """
    CSV data exporter keeps common output data format
    """
    def __init__(self, csv_folder_path: str, output_file_path: str):
        self._csv_folder_path = csv_folder_path
        self._folder_path = output_file_path

    def export(self):
        for *_, files in os.walk(self._csv_folder_path):
            for file_name in files:
                if file_name.endswith(".csv"):
                    self._export(file_name)

    def _export(self, file_name: str):
        source_file = os.path.join(self._csv_folder_path, file_name)
        with open(source_file) as f:
            reader = csv.DictReader(f)
            transformer = get_transformer(reader.fieldnames)
            self._write_to_file(file_name, reader, transformer)

    def _write_to_file(self, file_name: str, reader: csv.DictReader, transformer: BankDataLineTransformer):
        output_file_path = os.path.join(self._folder_path, file_name)
        with open(output_file_path, "w") as out:
            writer = csv.DictWriter(out, transformer.fields)
            writer.writeheader()
            for line in reader:
                writer.writerow(transformer.transform(line))
