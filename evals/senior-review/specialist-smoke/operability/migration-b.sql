ALTER TABLE customers ADD COLUMN display_name TEXT;
UPDATE customers SET display_name = name;
