import abc
import copy
import datetime
from typing import Any, Dict, Iterable, List, Optional

COMMON_DATE_FORMAT = "%d-%m-%Y"
VALID_TRANSACTIONS_TYPE = ["remove", "add"]


class AbstractField(abc.ABC):
    """
    Validates and transforms field's value
    """
    @abc.abstractmethod
    def validate(self, line: Dict) -> Any:
        pass

    @abc.abstractmethod
    def transform(self, line: Dict) -> Dict:
        pass


class TypedField(AbstractField):
    """
    Validates field type is expected format
    """

    def __init__(self, name: str, field_type: type, from_field: Optional[str] = None):
        if not isinstance(field_type, type):
            raise ValueError(f"Field type expected to be type type, got {type(field_type)}")
        self.type = field_type
        self.name = name
        self.from_field = from_field or name

    def validate(self, line: Dict) -> Any:
        try:
            value = line[self.from_field]
        except KeyError:
            raise ValueError(f"Field {self.from_field} not found in the line")
        if not isinstance(value, self.type):
            raise ValueError(f"Field type {line} has improper type, expected {self.type}, got {type(line)}")
        return value

    def transform(self, line: Dict) -> Dict:
        return {self.name: self.validate(line)}


class DateField(TypedField):
    """
    Validates and transforms date fields into common format
    """

    def __init__(self, name: str, field_type: type, fmt: str, from_field: Optional[str] = None):
        super().__init__(name, field_type, from_field)
        self._format = fmt

    def validate(self, line: Dict) -> datetime.datetime:
        value = super().validate(line)
        try:
            date = datetime.datetime.strptime(value, self._format)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Unexpected timestamp format, expected {self._format}, got {value}") from exc
        return date

    def transform(self, line: Dict) -> Dict:
        validated_field = self.validate(line)
        return {self.name: validated_field.strftime(COMMON_DATE_FORMAT)}


class OneOfField(TypedField):
    """
    Validates the field value is one of the values in the scope
    """

    def __init__(self, name: str, field_type: type, scope: List[str], from_field: Optional[str] = None):
        super().__init__(name, field_type, from_field)
        self.scope = self._validate_scope(scope)

    def _validate_scope(self, scope: List[str]) -> List[str]:
        for item in scope:
            if not isinstance(item, str):
                raise ValueError(f"Scope items expected to be str, got {type(item)}")
        return scope.copy()

    def validate(self, line: Dict) -> str:
        value = super().validate(line)
        if value not in self.scope:
            ValueError(f"{value} is not in the list of values: {self.scope}")
        return value


class MonetaryField(AbstractField):
    def __init__(self, name: str, euro: TypedField, cents: TypedField):
        self._euro = euro
        self._cents = cents
        self.name = name

    @property
    def from_field(self):
        return [self._euro.from_field, self._cents.from_field]

    def validate(self, line: Dict) -> Dict:
        return {self._euro.name: self._euro.validate(line), self._cents.name: self._cents.validate(line)}

    def transform(self, line: Dict) -> Dict:
        values = self.validate(line)
        combined_value = float(f"{values[self._euro.name]}.{values[self._cents.name]}")
        return {self.name: combined_value}


class BankDataLineTransformer:
    """
    Transforms the line of the data into format according to the provided schema
    """

    def __init__(self, schema: Iterable[AbstractField]):
        self._schema = self._validate_schema(schema)

    @property
    def fields(self):
        return [field.name for field in self._schema]

    @property
    def schema_fields(self):
        fields = []
        for field in self._schema:
            if isinstance(field.from_field, list):
                fields.extend(field.from_field)
            else:
                fields.append(field.from_field)
        return fields

    def _validate_schema(self, schema: Iterable[AbstractField]) -> Iterable[AbstractField]:
        for field_type in schema:
            if not isinstance(field_type, AbstractField):
                raise ValueError(f"Fields types expected to be type AbstractField, got {type(field_type)}")
        return copy.deepcopy(schema)

    def transform(self, line: Dict) -> dict:
        transformed = {}
        for field in self._schema:
            transformed.update(field.transform(line))
        return transformed


bank_1_schema = (
    DateField(name="date", field_type=str, fmt="%b %d %Y", from_field="timestamp"),
    OneOfField(name="transaction", field_type=str, scope=VALID_TRANSACTIONS_TYPE, from_field="type"),
    TypedField(name="amount", field_type=str),
    TypedField(name="from", field_type=str),
    TypedField(name="to", field_type=str),
)


bank_2_schema = (
    DateField(name="date", field_type=str, fmt=COMMON_DATE_FORMAT, from_field="date"),
    OneOfField(name="transaction", field_type=str, scope=VALID_TRANSACTIONS_TYPE),
    TypedField(name="amount", field_type=str, from_field="amounts"),
    TypedField(name="from", field_type=str),
    TypedField(name="to", field_type=str),
)


bank_3_schema = (
    DateField(name="date", field_type=str, fmt="%d %b %Y", from_field="date_readable"),
    OneOfField(name="transaction", field_type=str, scope=VALID_TRANSACTIONS_TYPE, from_field="type"),
    MonetaryField(
        name="amount", euro=TypedField(name="euro", field_type=str), cents=TypedField(name="cents", field_type=str)
    ),
    TypedField(name="from", field_type=str),
    TypedField(name="to", field_type=str),
)


registered_transformers = (
    BankDataLineTransformer(bank_1_schema),
    BankDataLineTransformer(bank_2_schema),
    BankDataLineTransformer(bank_3_schema),
)


def get_transformer(fields: List[str]) -> BankDataLineTransformer:
    for transformer in registered_transformers:
        if set(fields) == set(transformer.schema_fields):
            return transformer
    raise ValueError(f"FieldTransformer for these fields {fields} is not registered")
