from app.repositories.table_repository import TableRepository


class TableService:
    @staticmethod
    def list_active_tables():
        return TableRepository.list_active()

    @staticmethod
    def list_active_tables_grouped_by_floor():
        floor_groups = []
        floor_index = {}
        for table in TableRepository.list_active():
            floor = table.get("floor") or "未分樓層"
            if floor not in floor_index:
                floor_index[floor] = {"floor": floor, "tables": []}
                floor_groups.append(floor_index[floor])
            floor_index[floor]["tables"].append(table)
        return floor_groups

    @staticmethod
    def get_active_table(table_number):
        return TableRepository.get_active_by_number(str(table_number).strip())
