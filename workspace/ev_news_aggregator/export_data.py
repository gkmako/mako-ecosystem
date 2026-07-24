"""
Скрипт для экспорта данных из SQLite в CSV.
"""
import argparse
from src.storage import export_to_csv_from_sqlite
from src.config import settings

def main():
    parser = argparse.ArgumentParser(description='Экспорт данных из SQLite в CSV')
    parser.add_argument(
        '--db-path', 
        default=settings.SQLITE_DB_PATH,
        help='Путь к файлу базы данных SQLite'
    )
    parser.add_argument(
        '--csv-path',
        default='data/export.csv',
        help='Путь к выходному CSV файлу'
    )
    
    args = parser.parse_args()
    
    print(f"Экспорт данных из {args.db_path} в {args.csv_path}")
    export_to_csv_from_sqlite(args.db_path, args.csv_path)
    print("Экспорт завершен успешно!")

if __name__ == "__main__":
    main()