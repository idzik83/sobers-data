import abc
import copy
import datetime
from collections import OrderedDict
from typing import Any, Dict, List


COMMON_DATE_FORMAT = "%d-%m-%Y"
VALID_TRANSACTIONS_TYPE = ["remove", "add"]


class AbstractField(abc.ABC):
    """
    Validates and transforms field's value
    """
    @abc.abstractmethod
    def validate(self, value: Any) -> Any:
        pass

    @abc.abstractmethod
    def transform(self, value: Any) -> Dict:
        pass


class TypedField(AbstractField):
    """
    Validates field type is expected format
    """
    def __init__(self, name: str, field_type: type):
        if not isinstance(field_type, type):
            raise ValueError(f"Field type expected to be type type, got {type(field_type)}")
        self._type = field_type
        self.name = name

    def validate(self, value: Any) -> Any:
        if not isinstance(value, self._type):
            raise ValueError(f"Field type {value} has improper type, expected {self._type}, got {type(value)}")
        return value

    def transform(self, value: Any) -> Dict:
        return {self.name: self.validate(value)}


class DateField(TypedField):
    """
    Validates and transforms date fields into common format
    """
    def __init__(self, name: str, field_type: type, fmt: str):
        super().__init__(name, field_type)
        self._format = fmt

    def validate(self, value: str) -> datetime.datetime:
        try:
            date = datetime.datetime.strptime(value, self._format)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Unexpected timestamp format, expected {self._format}, got {value}") from exc
        return date

    def transform(self, value: str) -> Dict:
        validated_field = self.validate(value)
        return {self.name: validated_field.strftime(COMMON_DATE_FORMAT)}


class OneOfField(TypedField):
    """
    Validates the field value is one of the values in the scope
    """
    def __init__(self, name: str, field_type: type, scope: List[str]):
        super().__init__(name, field_type)
        self.scope = self._validate_scope(scope)

    def _validate_scope(self, scope: List[str]) -> List[str]:
        for item in scope:
            if not isinstance(item, str):
                raise ValueError(f"Scope items expected to be str, got {type(item)}")
        return scope.copy()

    def validate(self, value: str) -> str:
        if value not in self.scope:
            ValueError(f"{value} is not in the list of values: {self.scope}")
        return value


class BankDataLineTransformer:
    """
    Transforms the line of the data into format according to the provided schema
    """
    def __init__(self, schema: Dict[str, AbstractField]):
        self._schema = self._validate_schema(schema)

    @property
    def fields(self):
        return [field.name for _, field in self._schema.items()]

    @property
    def schema_fields(self):
        return self._schema.keys()

    def _validate_schema(self, schema: Dict[str, AbstractField]):
        for field_name, field_type in schema.items():
            if not isinstance(field_name, str):
                raise ValueError(f"Fields names expected to be type str, got {type(field_name)}")
            if not isinstance(field_type, AbstractField):
                raise ValueError(f"Fields types expected to be type AbstractField, got {type(field_type)}")
        return copy.deepcopy(schema)

    def transform(self, line: dict) -> dict:
        transformed = {}
        for field, value in line.items():
            try:
                transformer = self._schema[field]
            except KeyError:
                raise ValueError(
                    f"Field name {field} is unexpected by the schema, expected fields: {list(self._schema.keys())}"
                )
            transformed.update(transformer.transform(value))
        return transformed


class BankDataEuroCentsLineTransformer(BankDataLineTransformer):
    """
    Merges line containing euros and cents values into single amount field
    """

    @property
    def fields(self):
        return ["date", "transaction", "amount", "from", "to"]

    def transform(self, line: dict) -> dict:
        transformed = super().transform(line)
        try:
            euro = transformed.pop("euro")
            cents = transformed.pop("cents")
        except KeyError:
            raise ValueError(f"Fields euro or cents are not found in the line: {line}")
        transformed["amount"] = float(f"{euro}.{cents}")
        return transformed


bank_1_schema = OrderedDict({
    "timestamp": DateField("date", str, "%b %d %Y"),
    "type": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "amount": TypedField("amount", str),
    "from": TypedField("from", str),
    "to": TypedField("to", str)
})


bank_2_schema = OrderedDict({
    "date": DateField("date", str, COMMON_DATE_FORMAT),
    "transaction": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "amounts": TypedField("amount", str),
    "from": TypedField("from", str),
    "to": TypedField("to", str)
})


bank_3_schema = OrderedDict({
    "date_readable": DateField("date", str, "%d %b %Y"),
    "type": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "euro": TypedField("euro", str),
    "cents": TypedField("cents", str),
    "from": TypedField("from", str),
    "to": TypedField("to", str)
})


registered_transformers = (
    BankDataLineTransformer(bank_1_schema),
    BankDataLineTransformer(bank_2_schema),
    BankDataEuroCentsLineTransformer(bank_3_schema)
)


def get_transformer(fields: List[str]) -> BankDataLineTransformer:
    for transformer in registered_transformers:
        if set(fields) == set(transformer.schema_fields):
            return transformer
    raise ValueError(f"FieldTransformer for these fields {fields} is not registered")
