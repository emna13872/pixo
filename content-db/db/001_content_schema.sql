-- Pixo : base de CONTENU pédagogique (Supabase / Postgres)
-- ---------------------------------------------------------------
-- Ce script crée la base de contenu, séparée de la base de progression (enfants, scores).
-- Principe : chaque document (programme, séance, mot, média, objectif) est stocké ENTIER
-- en JSON (colonne JSONB). Pas de découpage en dizaines de tables.
--
--   content_schema      les schémas JSON (une ligne par type de document)
--   content_document    les documents en cours d'édition (la version de travail)
--   content_version     les versions publiées : FIGÉES, on ne peut ni les modifier ni les effacer
--   published_session   les fichiers livrés au moteur (format de Viven), un par séance et par version
--
-- Fichiers (images, chansons, vidéos) : bucket Storage « content-media ».
-- À lancer dans Supabase > SQL Editor, sur un projet de TEST d'abord.
-- Explications : content-db/docs/09-base-de-donnees.md
-- ---------------------------------------------------------------

create extension if not exists pg_jsonschema;   -- vérifier un JSON contre son schéma

-- 1. Les schémas JSON ---------------------------------------------------------
create table if not exists content_schema (
  doc_type    text primary key check (doc_type in ('program','session','word','media','objective','delivered-session')),
  schema      jsonb not null,
  updated_at  timestamptz not null default now()
);
comment on table content_schema is 'Une ligne par type : le contenu de content-db/schemas/<type>.schema.json';

-- 2. Les documents en édition ---------------------------------------------------
create table if not exists content_document (
  id          text primary key,                                   -- id permanent : w_hello, u1-s1...
  doc_type    text not null references content_schema(doc_type),
  version     integer not null check (version >= 1),
  status      text not null check (status in ('draft','published','archived')),
  body        jsonb not null,                                     -- le document entier
  updated_at  timestamptz not null default now(),
  updated_by  text not null,
  constraint body_matches_columns check (
    body->>'id' = id and body->>'type' = doc_type and (body->>'version')::int = version and body->>'status' = status
  )
);
create index if not exists content_document_type_idx on content_document (doc_type);
create index if not exists content_document_body_idx on content_document using gin (body jsonb_path_ops);
comment on table content_document is 'Version de travail de chaque document. Les séances citent mots, objectifs et médias par id.';

-- Vérification du schéma JSON à chaque écriture
create or replace function content_check_schema() returns trigger language plpgsql as $$
declare s jsonb;
begin
  select schema into s from content_schema where doc_type = new.doc_type;
  if s is null then
    raise exception 'Pas de schéma pour le type %', new.doc_type;
  end if;
  if not jsonb_matches_schema(s::json, new.body) then
    raise exception 'Le document % ne respecte pas le schéma %', new.id, new.doc_type;
  end if;
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists content_document_schema on content_document;
create trigger content_document_schema before insert or update on content_document
  for each row execute function content_check_schema();

-- 3. Les versions publiées (figées) --------------------------------------------
create table if not exists content_version (
  id            text not null,
  version       integer not null,
  doc_type      text not null,
  body          jsonb not null,
  published_at  timestamptz not null default now(),
  published_by  text not null,
  primary key (id, version)
);
comment on table content_version is 'Copie figée de chaque document publié. Corriger = publier la version suivante.';

create or replace function content_frozen() returns trigger language plpgsql as $$
begin
  raise exception 'Version publiée figée : on ne la modifie pas, on publie la version suivante';
end $$;

drop trigger if exists content_version_frozen on content_version;
create trigger content_version_frozen before update or delete on content_version
  for each row execute function content_frozen();

-- 4. Les fichiers livrés au moteur ---------------------------------------------
create table if not exists published_session (
  session_id    text not null,
  version       integer not null,
  delivered     jsonb not null,           -- exactement published/<séance>.v<version>.json
  channel       text not null default 'test' check (channel in ('test','release')),
  published_at  timestamptz not null default now(),
  primary key (session_id, version),
  constraint delivered_matches check (delivered->>'id' = session_id and (delivered->>'version')::int = version)
);
comment on table published_session is 'Ce que le moteur télécharge. test = tests internes, release = vrais enfants (licences validées).';

drop trigger if exists published_session_frozen on published_session;
create trigger published_session_frozen before update or delete on published_session
  for each row execute function content_frozen();

-- Le moteur demande : « la dernière version de la séance u1-s1 »
create or replace view latest_published_session as
  select distinct on (session_id) session_id, version, channel, delivered, published_at
  from published_session
  order by session_id, version desc;

-- 5. Sécurité (RLS) -------------------------------------------------------------
-- Lecture : tout utilisateur connecté (le moteur, l'app). Écriture : le rôle service (outil de publication)
-- et les éditeurs de contenu (à brancher sur Supabase Auth plus tard).
alter table content_schema    enable row level security;
alter table content_document  enable row level security;
alter table content_version   enable row level security;
alter table published_session enable row level security;

drop policy if exists read_published on published_session;
create policy read_published on published_session for select to authenticated using (true);
drop policy if exists read_documents on content_document;
create policy read_documents on content_document for select to authenticated using (true);
drop policy if exists read_versions on content_version;
create policy read_versions on content_version for select to authenticated using (true);
drop policy if exists read_schemas on content_schema;
create policy read_schemas on content_schema for select to authenticated using (true);
-- Pas de policy d'écriture : seul le rôle service_role (qui ignore RLS) écrit, via l'outil de publication.

-- 6. Stockage des fichiers ------------------------------------------------------
insert into storage.buckets (id, name, public)
values ('content-media', 'content-media', false)
on conflict (id) do nothing;
