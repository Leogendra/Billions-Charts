import os




def create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)


def normalize_date_for_comparison(date: str, precision: str) -> str:
    if (precision == "month"):
        return date + "-01"
    if (precision == "year"):
        return date + "-01-01"
    return date