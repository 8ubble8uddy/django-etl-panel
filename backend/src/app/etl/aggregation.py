from typing import Dict, Tuple

import pandas as pd

from app.models import Relationship


class Aggregation:
    """ETL-сервис агрегации данных датафреймов."""

    @staticmethod
    def get_column(dfs: Dict[str, pd.DataFrame], relation: Relationship, idx_col: str, tbl: str) -> pd.DataFrame:
        """Объединения связанных таблиц по определенным параметрам и получения новой колонки из полученных данных.

        Args:
            dfs: Датафреймы связанных таблицы
            relation: Метаинформация о связях таблиц
            idx_col: Название колонки для индексации данных
            tbl: Название родительской таблицы для группировки по ней

        Returns:
            pd.DataFrame: Датафрейм, состоящий из полученной колонки
        """
        return (
            pd.merge(
                left=dfs[relation.through_table].drop(idx_col, axis='columns'),
                right=dfs[relation.table],
                how='left',
                left_on=relation.table + relation.suffix,
                right_on=idx_col,
            )
            .query(relation.condition if relation.condition is not None else 'index == index')
            .groupby(by=tbl + relation.suffix)[[col.name for col in relation.model.columns.all()]]
            .apply(func=lambda row: list(row.to_numpy().flat) if relation.flat else row.to_dict('records'))
            .to_frame(relation.related_name)
        )

    @staticmethod
    def get_data_changes(src: pd.DataFrame, dest: pd.DataFrame, idx_col: str) -> Tuple[pd.DataFrame, ...]:
        """Функция для сравения датафреймов таблиц источника и получателя данных.

        Args:
            src: Датафрейм источника
            dest: Датафрейм получателя
            idx_col: Название колонки для индексации данных

        Returns:
            tuple[pandas.DataFrame, ...]: Датафреймы с новыми, обновленными и удаленными данными
        """
        dest.set_index(idx_col, inplace=True, drop=False)
        changes = src[~src.apply(tuple, axis='columns').isin(dest.apply(tuple, axis='columns'))]
        deleted = dest[  # type: ignore[call-overload]
            ~dest.apply(tuple, axis='columns').isin(src.apply(tuple, axis='columns'))
        ].drop(changes.index.values, errors='ignore')
        if not changes.empty:
            new = changes[~changes[idx_col].isin(dest[idx_col])]
            modified = changes[changes[idx_col].isin(dest[idx_col])]
        else:
            new, modified = changes, changes
        return new, modified, deleted
