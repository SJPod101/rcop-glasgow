-- RCoP Glasgow Branch dashboard shared-data schema.
-- Status: draft only. Do not run until the access model is confirmed.
--
-- This is designed for a public GitHub Pages dashboard using Supabase as the
-- shared store. It keeps the RCoP tables separate from existing integration
-- tables and enables RLS on every new public table.

create extension if not exists pgcrypto;

create table if not exists public.rcop_action_requests (
  id uuid primary key default gen_random_uuid(),
  area text not null,
  requester_name text,
  request_summary text not null,
  request_detail text,
  status text not null default 'new',
  whatsapp_shared boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rcop_open_questions (
  id uuid primary key default gen_random_uuid(),
  question text not null,
  owner text,
  needed_for text,
  status text not null default 'open',
  source text not null default 'dashboard',
  created_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rcop_question_responses (
  id uuid primary key default gen_random_uuid(),
  question_id uuid references public.rcop_open_questions(id) on delete cascade,
  responder_name text,
  response text not null,
  whatsapp_shared boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists public.rcop_asset_submissions (
  id uuid primary key default gen_random_uuid(),
  area text not null,
  contributor_name text,
  title text,
  notes text,
  file_name text,
  file_path text,
  mime_type text,
  status text not null default 'received',
  created_at timestamptz not null default now()
);

alter table public.rcop_action_requests enable row level security;
alter table public.rcop_open_questions enable row level security;
alter table public.rcop_question_responses enable row level security;
alter table public.rcop_asset_submissions enable row level security;

-- OPTION A: low-friction public dashboard link.
-- Anyone with the link can read and submit, but cannot update or delete.
-- This suits a volunteer working hub, but it is not private.

create policy "Anyone with link can read action requests"
  on public.rcop_action_requests
  for select
  to anon
  using (true);

create policy "Anyone with link can submit action requests"
  on public.rcop_action_requests
  for insert
  to anon
  with check (
    length(trim(area)) > 0
    and length(trim(request_summary)) > 0
  );

create policy "Anyone with link can read open questions"
  on public.rcop_open_questions
  for select
  to anon
  using (true);

create policy "Anyone with link can add open questions"
  on public.rcop_open_questions
  for insert
  to anon
  with check (length(trim(question)) > 0);

create policy "Anyone with link can read question responses"
  on public.rcop_question_responses
  for select
  to anon
  using (true);

create policy "Anyone with link can answer questions"
  on public.rcop_question_responses
  for insert
  to anon
  with check (length(trim(response)) > 0);

create policy "Anyone with link can read asset submissions"
  on public.rcop_asset_submissions
  for select
  to anon
  using (true);

create policy "Anyone with link can log asset submissions"
  on public.rcop_asset_submissions
  for insert
  to anon
  with check (length(trim(area)) > 0);

-- OPTION B: team-login dashboard.
-- If the dashboard should be private, replace the anon policies above with
-- authenticated-only policies and add Supabase Auth/magic links before launch.
