import abc
import csv
import copy
from pathlib import Path
from typing import Any, Dict, Union

from pydantic import BaseModel

from .models import registered_models


# class BankDataValidator:
#     def __init__(self, schema: Dict[str, type]):
#         self._schema = self._validate_schema(schema)
#
#     def _validate_schema(self, schema: Dict[str, type]):
#         for field_name, field_type in schema.keys():
#             if not isinstance(field_name, str):
#                 raise ValueError(f"Fields names expected to be type str, got {type(field_name)}")
#             if not isinstance(field_type, type):
#                 raise ValueError(f"Fields types expected to be type type, got {type(field_type)}")
#         return copy.deepcopy(schema)
#
#     def validate(self, line: Dict[str, Any]):
#         for field, value in line.keys():
#             if field not in self._schema:
#                 raise ValueError(
#                     f"Field name {field} is unexpected by the schema, expected fields: {list(self._schema.keys())}"
#                 )
#             expected_type = self._schema[field]
#             if not isinstance(value, expected_type):
#                 raise ValueError(
#                     f"Field type {value} has improper type, expected {expected_type}, got {type(value)}"
#                 )


# class BankDataLineTransformer:
#     def __init__(self, schema: BaseModel):
#         self._schema = schema
#
#     def transform(self, line: dict) -> dict:
#         line_obj = self._schema.validate(line)
#         return line_obj.dict()


class CSVBankDataIterator(metaclass=abc.ABCMeta):
    def __init__(self, csv_path: Union[str, Path], transformer: BaseModel):
        self._reader = self._get_reader(csv_path)
        self._transformer = transformer

    def _get_reader(self, csv_path: str) -> csv.DictReader:
        with open(csv_path) as f:
            return csv.DictReader(f)

    def __iter__(self):
        return self

    def __next__(self):
        for line in self._reader:
            yield self._transformer.dict(line)
