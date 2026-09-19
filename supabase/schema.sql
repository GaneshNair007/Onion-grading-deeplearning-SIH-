-- ONION-Q Supabase schema (run once in the Supabase SQL editor)
create table if not exists onion_reports (
  report_id      text primary key,
  batch_id       text,
  center_id      text,
  inspector_id   text,
  policy_id      text,
  policy_version text,
  model_versions jsonb,
  summary        jsonb,
  onions         jsonb,
  integrity_hash text,
  qr_payload     text,
  payload        jsonb,
  created_at     timestamptz not null default now()
);
alter table onion_reports enable row level security;

-- Public read for dashboards; writes ONLY via the service key.
create policy "public read reports" on onion_reports
  for select using (true);

-- Optional: audit trail of inspector overrides
create table if not exists onion_overrides (
  id            uuid primary key default gen_random_uuid(),
  report_id     text,
  inspector_id  text,
  original      jsonb,
  final         jsonb,
  reason_code   text,
  note          text,
  created_at    timestamptz not null default now()
);
alter table onion_overrides enable row level security;
create policy "public read overrides" on onion_overrides for select using (true);
