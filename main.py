import argparse

from sobers_data.csv_exporter import CSVBankDataExporter


parser = argparse.ArgumentParser(description='CSV Bank data exporter')
parser.add_argument('-p', '--path', metavar='path', type=str, help='the path to CSV folder')
parser.add_argument('-o', '--output', metavar='path', type=str, help='output folder path')


if __name__ == '__main__':
    args = parser.parse_args()
    csv_exporter = CSVBankDataExporter(args.path, args.output)
    csv_exporter.export()
