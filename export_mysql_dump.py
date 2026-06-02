import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "dogana.db"
MYSQL_DUMP_PATH = BASE_DIR / "dogana_mysql_import.sql"
BATCH_SIZE = 500


def quote_identifier(identifier):
    return f"`{identifier.replace('`', '``')}`"


def quote_value(value):
    if value is None:
        return "NULL"
    text = str(value)
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "''")
    return f"'{text}'"


def fetch_columns(db):
    return [
        row["column_name"]
        for row in db.execute(
            "SELECT column_name FROM column_metadata ORDER BY ordinal"
        )
    ]


def write_insert_batch(out, table_name, columns, rows):
    if not rows:
        return

    column_list = ", ".join(quote_identifier(column) for column in columns)
    out.write(f"INSERT INTO {quote_identifier(table_name)} ({column_list}) VALUES\n")
    values = []
    for row in rows:
        values.append("(" + ", ".join(quote_value(row[column]) for column in columns) + ")")
    out.write(",\n".join(values))
    out.write(";\n\n")


def export():
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"Missing SQLite database: {SQLITE_PATH}")

    db = sqlite3.connect(SQLITE_PATH)
    db.row_factory = sqlite3.Row
    columns = fetch_columns(db)

    with MYSQL_DUMP_PATH.open("w", encoding="utf-8", newline="\n") as out:
        out.write("-- Dogana voter database import for MySQL/MariaDB/phpMyAdmin\n")
        out.write("SET NAMES utf8mb4;\n")
        out.write("SET FOREIGN_KEY_CHECKS = 0;\n\n")

        out.write("DROP TABLE IF EXISTS `column_metadata`;\n")
        out.write("DROP TABLE IF EXISTS `voters`;\n\n")

        voter_columns = ",\n  ".join(
            f"{quote_identifier(column)} TEXT NULL" for column in columns
        )
        out.write(
            "CREATE TABLE `voters` (\n"
            "  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,\n"
            f"  {voter_columns},\n"
            "  PRIMARY KEY (`id`),\n"
            "  KEY `idx_voters_uniqueid` (`uniqueid`(191)),\n"
            "  KEY `idx_voters_first_name` (`first_name`(191)),\n"
            "  KEY `idx_voters_last_name` (`last_name`(191)),\n"
            "  KEY `idx_voters_fathers_name` (`fathers_name`(191)),\n"
            "  KEY `idx_voters_admin_unit` (`admin_unit`(191)),\n"
            "  KEY `idx_voters_qv` (`qv`(191)),\n"
            "  KEY `idx_voters_shtab` (`shtab`(191))\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        out.write(
            "CREATE TABLE `column_metadata` (\n"
            "  `column_name` VARCHAR(191) NOT NULL,\n"
            "  `original_header` VARCHAR(255) NOT NULL,\n"
            "  `ordinal` INT NOT NULL,\n"
            "  PRIMARY KEY (`column_name`)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n\n"
        )

        metadata_rows = list(
            db.execute(
                "SELECT column_name, original_header, ordinal FROM column_metadata ORDER BY ordinal"
            )
        )
        write_insert_batch(
            out,
            "column_metadata",
            ["column_name", "original_header", "ordinal"],
            metadata_rows,
        )

        batch = []
        voter_columns = ["id", *columns]
        for row in db.execute(f"SELECT {', '.join(quote_identifier(c) for c in voter_columns)} FROM voters ORDER BY id"):
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                write_insert_batch(out, "voters", voter_columns, batch)
                batch.clear()
        write_insert_batch(out, "voters", voter_columns, batch)

        out.write(
            "CREATE OR REPLACE VIEW `voter_search` AS\n"
            "SELECT\n"
            "  `id`, `uniqueid`, `first_name`, `last_name`, `fathers_name`,\n"
            "  `mothers_name`, `birthday`, `age`, `gender`, `admin_unit`,\n"
            "  `shtab`, `os`, `qv`, `qv_ranking_no`, `building_no`,\n"
            "  `political_preference`, `phone_number`, `emigrant`\n"
            "FROM `voters`;\n\n"
        )
        out.write("SET FOREIGN_KEY_CHECKS = 1;\n")

    print(f"Created {MYSQL_DUMP_PATH.name}")
    print(f"Rows exported: {db.execute('SELECT COUNT(*) FROM voters').fetchone()[0]}")


if __name__ == "__main__":
    export()
