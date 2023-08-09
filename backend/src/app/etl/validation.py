import builtins
import datetime
import uuid
from typing import Any, Dict, List, Type

import pandas
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from pydantic import BaseModel, Field, ValidationError, create_model, validator
from pydantic.fields import FieldInfo, ModelField

from app.etl.errors import TransformError
from app.models import Column, Model, Relationship


class Validation(BaseModel):
    """ETL-сервис валидации и трансформации данных."""

    class Config:
        """Настройки валидации."""

        allow_population_by_field_name = True
        arbitrary_types_allowed = True

    @validator('*', pre=True)
    def transform_default_value(cls, value: Any, field: ModelField) -> Any:
        """Преобразование пустых значений в значения по умолчанию.

        Args:
            value: Значение поля
            field: Метаданные поля

        Returns:
            Any: Значение после валидации
        """
        if not isinstance(value, list):
            return field.default if pandas.isna(value) else value
        return value

    @classmethod
    def get_schema(cls, model: Model, relations: QuerySet[Relationship]) -> Type['Validation']:
        """Получение динамической схемы для валидации данных.

        Args:
            model: Модель объекта
            relations: Данные о вложенных объектах

        Returns:
            Type[Validation]: Схема валидации данных
        """
        fields = cls.get_fields(model)
        for rel in relations:
            if not rel.flat:
                nested_type = create_model(rel.model.title, __base__=cls, **cls.get_fields(rel.model))
            else:
                nested_type = cls.get_type(rel.model.columns.first().type)
            fields[rel.related_name] = List[nested_type], Field(default=[])  # type: ignore[valid-type]
        return create_model(model.title, __base__=cls, **fields)

    @classmethod
    def get_fields(cls, model: Model) -> Dict:
        """Определение полей схемы.

        Args:
            model: Модель объекта

        Returns:
            Dict: Поля схемы
        """
        mapping = {}
        for col in model.columns.all():
            mapping[col.name] = cls.get_type(col.type), cls.get_field_info(col)
        return mapping

    @classmethod
    def get_type(cls, value: str) -> Type:
        """Приведение строкового представления типа данных в тип данных Python.

        Args:
            value: Строковое представление типа данных

        Returns:
            Type: Тип данных Python
        """
        if value == 'UUID':
            return getattr(uuid, value)
        if value in {'date', 'datetime'}:
            return getattr(datetime, value)
        else:
            return getattr(builtins, value)

    @classmethod
    def get_field_info(cls, column: Column) -> FieldInfo:
        """Получение метаданных поля схемы.

        Args:
            column: Колонка модели

        Returns:
            FieldInfo: Метаданные поля
        """
        field_info = model_to_dict(column)
        if default_value := field_info.pop('default', None):
            if default_value == 'None':
                field_info['default'] = None
            elif default_value in {'""', "''"}:
                field_info['default'] = ''
            else:
                field_info['default'] = default_value
        return Field(**field_info)

    @classmethod
    def validate_row(cls, row: pandas.Series) -> Dict:
        """Основной метод валидции строк в датафрейме.

        Args:
            row: Одномерный массив значений датафрейма

        Raises:
            TransformError: Ошибка трансформации данных

        Returns:
            Dict: Строка после обработки
        """
        try:
            data = pandas.Series(cls(**row).dict(by_alias=True))
        except ValidationError as exc:
            raise TransformError(exc.errors(), str(row.name))
        return data  # type: ignore[return-value]
