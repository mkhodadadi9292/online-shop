#!/bin/bash
# Creates one database per microservice (plus a *_test twin per service) on
# first Postgres container start. Dev and test data are fully isolated.
set -e

for db in \
  users_db catalog_db inventory_db orders_db payments_db \
  users_db_test catalog_db_test inventory_db_test orders_db_test payments_db_test; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE "$db";
EOSQL
done
