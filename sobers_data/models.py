import abc
import copy
import datetime
from typing import Any, Dict, List, Tuple

# from pydantic import BaseModel, ValidationError


COMMON_DATE_FORMAT = "%d-%m-%Y"
VALID_TRANSACTIONS_TYPE = ["remove", "add"]


# class BaseBankModel(BaseModel):
#     class Config:
#         fields = {"from_": "from"}
#         date_format = COMMON_DATE_FORMAT
#
#     from_: int
#     to: int
#
#     def date_to_common_format(self, value: str) -> str:
#         try:
#             date = datetime.datetime.strptime(value, self.Config.date_format)
#         except (ValueError, TypeError) as exc:
#             raise ValidationError(f"Unexpected timestamp format, expected {self.Config.date_format}, got {value}"
#                                   ) from exc
#         return date.strftime(COMMON_DATE_FORMAT)
#
#
# class Bank2Model(BaseBankModel):
#     class Config:
#         date_format = COMMON_DATE_FORMAT
#         fields = {"from_": "from"}
#
#     date: str
#     transaction: VALID_TRANSACTIONS_TYPE
#     amounts: float
#
#     def dict(self, *args, **kwargs):
#         return {
#             "date": self.date_to_common_format(self.date),
#             "transaction": self.transaction,
#             "amount": self.amounts,
#             "to": self.to,
#             "from": self.from_
#         }
#
#
# class Bank1Model(BaseBankModel):
#     class Config:
#         date_format = "%b %d %Y"
#         fields = {"from_": "from"}
#
#     timestamp: str
#     type: VALID_TRANSACTIONS_TYPE
#     amount: float
#
#     def dict(self, *args, **kwargs):
#         return {
#             "date": self.date_to_common_format(self.timestamp),
#             "transaction": self.type,
#             "amount": self.amount,
#             "to": self.to,
#             "from": self.from_
#         }
#
#
# class Bank3Model(BaseBankModel):
#     class Config:
#         date_format = "%d %b %Y"
#         fields = {"from_": "from"}
#
#     date_readable: str
#     type: VALID_TRANSACTIONS_TYPE
#     euro: int
#     cents: int
#
#     def dict(self, *args, **kwargs):
#         amount = float(f"{self.euro}.{self.cents}")
#         return {
#             "date": self.date_to_common_format(self.date_readable),
#             "transaction": self.type,
#             "amount": amount,
#             "to": self.to,
#             "from": self.from_
#         }


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
    def __init__(self, name: str, field_type: type):
        if not isinstance(field_type, field_type):
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
    def __init__(self, schema: Dict[str, AbstractField]):
        self._schema = self._validate_schema(schema)

    def _validate_schema(self, schema: Dict[str, AbstractField]):
        for field_name, field_type in schema.keys():
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
            new_field, value = transformer.transform(value)
            transformed[new_field] = value
        return transformed


class BankDataEuroCentsLineTransformer(BankDataLineTransformer):
    def transform(self, line: dict) -> dict:
        transformed = super().transform(line)
        euro = transformed["euro"]
        cents = transformed["cents"]
        transformed["amount"] = float(f"{euro}.{cents}")
        return transformed


bank_1_schema = {
    "timestamp": DateField("date", str, "%b %d %Y"),
    "type": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "amount": TypedField("amount", float),
    "from": TypedField("from", int),
    "to": TypedField("to", int)
}


bank_2_schema = {
    "date": DateField("date", str, COMMON_DATE_FORMAT),
    "transaction": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "amounts": TypedField("amount", float),
    "from": TypedField("from", int),
    "to": TypedField("to", int)
}


bank_3_schema = {
    "date_readable": DateField("date", str, "%d %b %Y"),
    "type": OneOfField("transaction", str, VALID_TRANSACTIONS_TYPE),
    "from": TypedField("from", int),
    "to": TypedField("to", int),
    "euro": TypedField("euro", int),
    "cents": TypedField("cents", int)
}


registered_models = (
    BankDataLineTransformer(bank_1_schema),
    BankDataLineTransformer(bank_2_schema),
    BankDataEuroCentsLineTransformer(bank_3_schema)
)
