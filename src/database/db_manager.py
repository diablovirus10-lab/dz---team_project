def create_tables(self):
    """Создать таблицы из schema.sql"""
    try:
        with open('data/schema.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            self.cursor.execute(sql)
            self.connection.commit()
            print("✅ Таблицы созданы/проверены")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        self.connection.rollback()