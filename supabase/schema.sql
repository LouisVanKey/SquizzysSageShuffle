-- Squizzy's Sage Shuffle - Hero Picker
-- Run this once in the Supabase SQL editor, then run seed_heroes.sql.

-- 1. Heroes that exist in the picker (seeded from seed_heroes.sql)
create table if not exists public.heroes (
  id       text primary key,
  name     text not null,
  pickable boolean not null default true      -- false = benched in Silver Age
);

-- 2. Event settings (single row). Set locks_open = false to freeze the picks.
create table if not exists public.settings (
  id         boolean primary key default true check (id),
  locks_open boolean not null default true
);
insert into public.settings (id) values (true) on conflict do nothing;

-- 3. Organisers, by Discord user ID (Discord > Settings > Advanced > Developer Mode,
--    then right-click your name > Copy User ID).
create table if not exists public.admins (
  discord_id text primary key,
  note       text
);

-- 4. The locks. One row per hero (primary key) and one row per Discord account (unique).
create table if not exists public.picks (
  hero_id      text primary key references public.heroes (id),
  -- NULL user_id = a pick added by hand by an organiser (player without Discord).
  user_id      uuid unique default auth.uid() references auth.users (id) on delete cascade,
  player_name  text not null check (char_length(btrim(player_name)) between 2 and 32),
  discord_name text check (char_length(discord_name) <= 64),
  created_at   timestamptz not null default now()
);

-- Admin check. Uses auth.identities, which users cannot edit themselves.
create or replace function public.is_admin()
returns boolean
language sql stable security definer set search_path = ''
as $$
  select exists (
    select 1
    from auth.identities i
    join public.admins a on a.discord_id = i.provider_id
    where i.user_id = auth.uid() and i.provider = 'discord'
  );
$$;

create or replace function public.can_pick(hero text)
returns boolean
language sql stable security definer set search_path = ''
as $$
  select (select locks_open from public.settings)
     and exists (select 1 from public.heroes h where h.id = hero and h.pickable);
$$;

-- The public Discord tag is filled in by the database from the verified Discord login,
-- so nobody can lock a hero under someone else's tag.
create or replace function public.set_discord_name()
returns trigger
language plpgsql security definer set search_path = ''
as $$
begin
  if auth.uid() is not null then
    select coalesce(i.identity_data ->> 'full_name', i.identity_data ->> 'name')
      into new.discord_name
      from auth.identities i
     where i.user_id = auth.uid() and i.provider = 'discord'
     limit 1;
  end if;
  return new;
end;
$$;
drop trigger if exists picks_set_discord_name on public.picks;
create trigger picks_set_discord_name before insert on public.picks
  for each row execute function public.set_discord_name();

-- Row level security
alter table public.heroes   enable row level security;
alter table public.settings enable row level security;
alter table public.admins   enable row level security;
alter table public.picks    enable row level security;

drop policy if exists "heroes are public"   on public.heroes;
drop policy if exists "settings are public" on public.settings;
drop policy if exists "admins edit settings" on public.settings;
drop policy if exists "picks are public"    on public.picks;
drop policy if exists "lock in own hero"    on public.picks;
drop policy if exists "admins remove picks" on public.picks;

create policy "heroes are public"   on public.heroes   for select using (true);
create policy "settings are public" on public.settings for select using (true);
create policy "admins edit settings" on public.settings for update to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- Hero locks are public.
create policy "picks are public" on public.picks for select using (true);

-- A signed-in player can insert exactly one row, for themselves, for a pickable hero.
-- There is deliberately no update policy: locked is locked.
create policy "lock in own hero" on public.picks for insert to authenticated
  with check (user_id = auth.uid() and public.can_pick(hero_id));

-- Only organisers can remove a lock.
create policy "admins remove picks" on public.picks for delete to authenticated
  using (public.is_admin());

grant select on public.heroes, public.settings, public.picks to anon, authenticated;
grant insert (hero_id, player_name) on public.picks to authenticated;
grant delete on public.picks to authenticated;
grant update (locks_open) on public.settings to authenticated;
grant execute on function public.is_admin(), public.can_pick(text) to anon, authenticated;

-- Live updates for everyone watching the page.
do $$ begin
  alter publication supabase_realtime add table public.picks;
exception when duplicate_object then null; end $$;

-- 5. Add the organisers (replace with real Discord user IDs):
-- insert into public.admins (discord_id, note) values ('123456789012345678', 'Louis'), ('234567890123456789', 'Brecht');
