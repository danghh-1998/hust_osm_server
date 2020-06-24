# HUST OSM Server

> Ứng dụng chỉ đường trong trường đại học Bách Khoa Hà Nội

## Cài đặt

### Postgresql

- Cài đặt __postgresql__ và __postgresql_contrib__

```bash
sudo apt update -y
sudo apt install postgresql postgresql-contrib -y
```

- Cài đặt __postgis__

```bash
sudo apt install postgis -y
```

- Tạo database

```bash
createdb osm;
```

- Thêm postgis extension vào database

```bash
psql
```

```sql
\c osm;
CREATE EXTENSION postgis;
\q
```

## Required packages

- Cài đặt package cần thiết

```bash
# Di chuyển vào thư mục chứa code
cd hust_osm_server
# Cài đặt package
pip install -r requirements.txt
```

## Flask

- Config database 

```python
DB_USER = 'db_user'
DB_PASSWORD = 'db_passwod'
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'osm'
```

- Import dữ liệu vào database

```bash
python db.py
```

- Khởi động Flask server

```bash
python api.py
```

