import os

import pandas as pd
from src.db.db_helper import DbHelper

class MuseumLoader:
    def __init__(self):
        self.db_helper = DbHelper()
        self.museums_df = None
        self.interests_dict = None


    @staticmethod
    def _clear_str(str_):
        """Очистка строки от HTML-тегов и лишних пробелов."""
        res_str = str_.replace('<p>', '')
        res_str = res_str.lstrip()
        res_str = res_str.lstrip('<span>')
        return res_str


    def _load_data_from_csv(self):
        """Загрузка данных из CSV-файла museums.csv в директории assets."""

        # Определяем путь к файлу museums.csv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
        assets_dir = os.path.join(root_dir, 'assets')
        csv_path = os.path.join(assets_dir, 'museums.csv')

        # Проверяем существование файла
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Файл museums.csv не найден в директории {assets_dir}")

        """Загрузка данных из CSV."""
        self.museums_df = pd.read_csv(
            csv_path,
            sep=',',
            usecols=["Название", "Описание", "Местоположение", "Улица", "Категории интересов"]
        )
        print("Данные из CSV успешно загружены.")


    def _clean_data(self):
        """Очистка и предобработка данных."""
        if self.museums_df is None:
            raise ValueError("Данные не загружены. Сначала нужно вызвать _load_data_from_csv.")

        # Удаляем строки с пустыми значениями в ключевых колонках
        self.museums_df = self.museums_df.dropna(subset=["Название", "Описание", "Местоположение", "Улица"])

        # Переименовываем колонки
        self.museums_df = self.museums_df.rename(columns={
            "Название": "name",
            "Описание": "description",
            "Местоположение": "city",
            "Улица": "street"
        })

        # Очищаем строки от HTML-тегов и лишних пробелов
        self.museums_df["name"] = self.museums_df["name"].apply(self._clear_str)
        self.museums_df["description"] = self.museums_df["description"].apply(self._clear_str)
        self.museums_df["city"] = self.museums_df["city"].apply(self._clear_str)
        self.museums_df["street"] = self.museums_df["street"].apply(self._clear_str)

        # Формируем колонку address
        self.museums_df["address"] = self.museums_df["city"] + ", " + self.museums_df["street"]

        # Удаляем ненужную колонку
        self.museums_df = self.museums_df.drop(columns=["street"])

        # Проверяем наличие колонки "Категории интересов"
        if "Категории интересов" in self.museums_df.columns:
            self.museums_df = self.museums_df.rename(columns={"Категории интересов": "relative_interests"})
            self.museums_df["relative_interests"] = self.museums_df["relative_interests"].apply(self._clear_str)
        else:
            # Если колонка отсутствует, создаем пустую колонку
            self.museums_df["relative_interests"] = None

        print("Данные успешно очищены и подготовлены.")


    def _load_interests_dict(self):
        """Загрузка словаря интересов из базы данных."""
        interests_df = self.db_helper.read_query("SELECT interest_id, interest_name FROM museum.interest")
        self.interests_dict = dict(zip(interests_df["interest_name"], interests_df["interest_id"]))
        print("Словарь интересов успешно загружен.")


    def _establish_interest_relations(self, museum_id, relative_interests):
        """Установление связей между музеем и интересами."""
        if pd.notna(relative_interests) and relative_interests:
            interests_list = [interest.strip() for interest in relative_interests.split(",")]
            for interest in interests_list:
                if interest in self.interests_dict:
                    query = '''
                        INSERT INTO museum.museum_interest (museum_id, interest_id)
                        VALUES (%s, %s)
                    '''
                    params = (museum_id, self.interests_dict[interest])
                    cursor = self.db_helper.connection.cursor()
                    cursor.execute(query, params)
                    self.db_helper.connection.commit()
                    cursor.close()


    def _save_data_to_db(self):
        """Сохранение данных в базу данных."""
        if self.museums_df is None:
            raise ValueError("Данные не загружены. Сначала нужно вызвать _load_data_from_csv.")

        if self.interests_dict is None:
            self._load_interests_dict()

        for _, row in self.museums_df.iterrows():
            # Вставляем музей
            query = '''
                INSERT INTO museum.museum (name, description, city, address)
                VALUES (%s, %s, %s, %s)
                RETURNING sk
            '''
            params = (
                row["name"],
                row["description"],
                row["city"],
                row["address"]
            )
            cursor = self.db_helper.connection.cursor()
            cursor.execute(query, params)
            museum_id = cursor.fetchone()[0]

            # Устанавливаем связи с интересами
            self._establish_interest_relations(museum_id, row["relative_interests"])

            cursor.close()

        print("Данные успешно сохранены в базу данных.")

    def load_museums(self):
        """Основной метод для загрузки музеев из CSV и сохранения в БД."""
        try:
            self._load_data_from_csv()
            self._clean_data()
            self._save_data_to_db()
        except Exception as e:
            print(f"Ошибка при загрузке музеев: {e}")
            self.db_helper.connection.rollback()
        finally:
            self.db_helper.close_connection()