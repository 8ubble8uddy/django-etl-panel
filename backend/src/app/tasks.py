import pandas
from celery import shared_task

from app.etl.operators import Join, Load, Select, Sync, Transform
from app.models import Process


@shared_task(name='transfer_data')
def transfer_data(process_id: int) -> str:
    """Функция для реализации одноразовой передачи данных.

    Args:
        process_id: Идентификатор процесса

    Returns:
        str: Результат передачи данных
    """
    process = Process.objects.get(id=process_id)
    df = (
        pandas.DataFrame()
        .pipe(Select, process.source, process.from_table)
        .pipe(Join, process.source, process.from_table, process.relationships.all(), process.index_col)
        .pipe(Transform, process.model, process.relationships.all())
        .pipe(Load, process.target, process.to_table)
    )
    return f'процесс={process}, загружено={df.inserted_rows}'


@shared_task(name='sync_data')
def sync_data(process_id: int) -> str:
    """Функция для реализации синхронизации данных между источником и целью.

    Args:
        process_id: Идентификатор процесса

    Returns:
        str: Результат передачи данных
    """
    process = Process.objects.get(id=process_id)
    df = (
        pandas.DataFrame()
        .pipe(Select, process.target, process.to_table)
        .pipe(Transform, process.model, process.relationships.all())
        .pipe(Sync, process.target, process.to_table, process.index_col, source_df=(
            pandas.DataFrame()
            .pipe(Select, process.source, process.from_table)
            .pipe(Join, process.source, process.from_table, process.relationships.all(), process.index_col)
            .pipe(Transform, process.model, process.relationships.all())
        ))
    )
    return f'процесс={process}, загружено={df.inserted_rows}, обновлено={df.updated_rows}, удалено={df.deleted_rows}'
