import pandas as pd
from django.db.models.query import QuerySet

from app.etl.aggregation import Aggregation
from app.etl.crud import CRUD
from app.etl.validation import Validation
from app.models import Database, Model, Relationship


class Select(pd.DataFrame):
    """ETL-оператор для извлечения данных из таблицы базы данных."""

    def __init__(self, df: pd.DataFrame, db: Database, tbl: str):
        """При инициализации ожидает получить данные об источнике.

        Args:
            df: Датафрейм
            db: Данные БД
            tbl: Название таблицы
        """
        engine = CRUD.get_engine(db.type)
        df = engine.read(db.uri, tbl)
        super().__init__(data=df)  # type: ignore[call-arg]


class Join(pd.DataFrame):
    """ETL-оператор для объединения таблиц по определённым параметрам и получния нужных данных."""

    def __init__(self, df: pd.DataFrame, db: Database, tbl: str, relations: QuerySet[Relationship], idx_col: str):
        """При инициализации ожидает получить данные об источнике вместе с присоединёнными таблицами.

        Args:
            df: Датафрейм
            db: Данные БД
            tbl: Название таблицы
            relations: Связи с другими таблицами
            idx_col: Колонка для индексации данных
        """
        if not df.empty:
            engine = CRUD.get_engine(db.type)
            dfs = {table: engine.read(db.uri, table) for rel in relations for table in (rel.table, rel.through_table)}
            new_columns = [Aggregation.get_column(dfs, rel, idx_col, tbl) for rel in relations]
            df = df.set_index(idx_col, drop=False).join(new_columns)  # type: ignore[arg-type]
        super().__init__(data=df)  # type: ignore[call-arg]


class Transform(pd.DataFrame):
    """ETL-оператор для валидации и трансформации данных."""

    def __init__(self, df: pd.DataFrame, model: Model, relations: QuerySet[Relationship]):
        """При инициализации ожидает получить данные модели передачи данных вместе с вложенными объектах.

        Args:
            df: Датафрейм
            model: Модель данных
            relations: Данные по связанным таблицам
        """
        if not df.empty:
            schema = Validation.get_schema(model, relations)
            df = df.apply(schema.validate_row, axis='columns')  # type: ignore[assignment]
        super().__init__(data=df)  # type: ignore[call-arg]


class Load(pd.DataFrame):
    """ETL-оператор для загрузки данных их получателю."""

    def __init__(self, df: pd.DataFrame, db: Database, tbl: str):
        """При инициализации ожидает получить данные о получателе.

        Args:
            df: Датафрейм
            db: Данные БД
            tbl: Название таблицы
        """
        inserted_rows = 0
        if not df.empty:
            engine = CRUD.get_engine(db.type)
            inserted_rows = engine.create(df, db.uri, tbl)
        super().__init__(data=df)  # type: ignore[call-arg]
        self.inserted_rows = inserted_rows


class Sync(pd.DataFrame):
    """ETL-оператор для синхронизации данных между источником и получателем."""

    def __init__(self, df: pd.DataFrame, db: Database, tbl: str, idx_col: str, source_df: pd.DataFrame):
        """При инициализации ожидает получить данные об источнике и получателе.

        Args:
            df: Датафрейм получателя
            db: Данные БД
            tbl: Название таблицы
            idx_col: Колонка для индексации данных
            source_df: Датафрейм источника
        """
        engine = CRUD.get_engine(db.type)
        inserted_rows, updated_rows, deleted_rows = 0, 0, 0
        if not df.empty:
            new, modified, deleted = Aggregation.get_data_changes(source_df, df, idx_col)
            inserted_rows = engine.create(new, db.uri, tbl) if not new.empty else 0
            updated_rows = engine.update(modified, db.uri, tbl) if not modified.empty else 0
            deleted_rows = engine.delete(deleted, db.uri, tbl) if not deleted.empty else 0
        else:
            inserted_rows = engine.create(source_df, db.uri, tbl) if not source_df.empty else 0
        super().__init__(data=df)  # type: ignore[call-arg]
        self.inserted_rows = inserted_rows
        self.updated_rows = updated_rows
        self.deleted_rows = deleted_rows
