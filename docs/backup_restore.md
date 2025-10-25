# Guia de Backup e Restore

1. Configure backups diários do PostgreSQL utilizando `pg_dump` direcionado para armazenamento seguro.
2. Armazene os arquivos XML e relatórios em volumes versionados (S3 opcional com versionamento).
3. Para restore completo:
   - Restaure o banco: `pg_restore` no snapshot desejado.
   - Recupere arquivos do storage e sincronize com `files.storage_path`.
   - Reprocessar auditorias executando `celery -A app.worker audit:rebuild`.
4. Teste periodicamente o processo em ambiente isolado.
