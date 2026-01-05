CREATE ROLE gymdb_test
WITH LOGIN PASSWORD 'gymdb_test';

CREATE DATABASE gymdb_test
OWNER gymdb_test;

REVOKE ALL ON DATABASE gymdb_test FROM PUBLIC;