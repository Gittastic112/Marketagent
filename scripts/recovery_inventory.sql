\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ;
SET LOCAL TIME ZONE 'UTC';
SET LOCAL DateStyle = 'ISO, YMD';
SET LOCAL extra_float_digits = 3;
CREATE TEMP TABLE mi_recovery_inventory (payload jsonb) ON COMMIT DROP;
DO $$
DECLARE item record; store text; column_name text; amount bigint; bytes bigint;
BEGIN
  FOR item IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename LOOP
    EXECUTE format(
      'INSERT INTO mi_recovery_inventory SELECT jsonb_build_object(''kind'', ''table'', ''name'', %L, ''rows'', count(*), ''sha256'', encode(sha256(convert_to(COALESCE(string_agg(row_hash, '''' ORDER BY row_hash COLLATE "C"), ''''), ''UTF8'')), ''hex'')) FROM (SELECT encode(sha256(convert_to(to_jsonb(t)::text, ''UTF8'')), ''hex'') AS row_hash FROM public.%I t) hashes',
      item.tablename, item.tablename);
  END LOOP;
  FOREACH store IN ARRAY ARRAY['document_assets', 'brief_sources'] LOOP
    column_name := CASE store WHEN 'document_assets' THEN 'content' ELSE 'pdf_bytes' END;
    IF to_regclass(format('public.%I', store)) IS NULL THEN
      INSERT INTO mi_recovery_inventory VALUES (jsonb_build_object('kind', 'asset_store', 'name', store, 'present', false, 'count', 0, 'content_bytes', 0));
    ELSE
      EXECUTE format('SELECT count(*), COALESCE(sum(octet_length(%I)), 0) FROM public.%I WHERE %I IS NOT NULL', column_name, store, column_name) INTO amount, bytes;
      INSERT INTO mi_recovery_inventory VALUES (jsonb_build_object('kind', 'asset_store', 'name', store, 'present', true, 'count', amount, 'content_bytes', bytes));
      EXECUTE format('INSERT INTO mi_recovery_inventory SELECT jsonb_build_object(''kind'', ''asset'', ''store'', %L, ''id'', id::text, ''size_bytes'', octet_length(%I), ''sha256'', encode(sha256(%I), ''hex'')) FROM public.%I WHERE %I IS NOT NULL', store, column_name, column_name, store, column_name);
    END IF;
  END LOOP;
END $$;
INSERT INTO mi_recovery_inventory
SELECT jsonb_build_object('kind', 'database', 'postgres_major', current_setting('server_version_num')::int / 10000, 'revisions', COALESCE(jsonb_agg(version_num ORDER BY version_num), '[]'::jsonb)) FROM public.alembic_version;
SELECT payload::text FROM mi_recovery_inventory ORDER BY payload->>'kind', payload->>'name', payload->>'store', payload->>'id';
COMMIT;
