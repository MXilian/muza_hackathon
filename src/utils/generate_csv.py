import csv
import os
import shutil

from src.interests import INTERESTS


# Создание CSV-файлов (по одному для каждой категории интересов)
def generate_csv():
    # Получаем абсолютный путь к OUTPUT_DIR
    output_path = os.path.abspath("../../assets/interests/")

    # Если директория существует, удаляем её вместе со всем содержимым
    if os.path.exists(output_path):
        shutil.rmtree(output_path)  # Удаляем директорию
        print(f"Директория {output_path} успешно удалена.")

    # Создаем директорию заново
    os.makedirs(output_path, exist_ok=True)  # Создаем директорию, если она не существует
    print(f"Директория {output_path} успешно создана.")

    for index, (category, interests) in enumerate(INTERESTS.items(), start=1):
        # Служебное название файла
        filename = f"category_{index}.csv"
        filepath = os.path.join(output_path, filename)

        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['interests'])  # Заголовок
            writer.writerow([category])     # Категория
            for interest in interests:      # Интересы
                writer.writerow([interest])

        print(f"Файл {filepath} успешно создан.")

if __name__ == "__main__":
    generate_csv()