-- 在 Supabase SQL Editor 执行此档案
-- Step 1: 建立 cards 资料表
create table if not exists cards (
  id          bigint primary key default (extract(epoch from now()) * 1000)::bigint,
  type        text not null,
  title       text,
  caption     text,
  desc        text,
  src         text,
  url         text,
  name        text,
  uploader    text,
  created_at  timestamptz default now()
);

-- Step 2: 开启 Row Level Security
alter table cards enable row level security;

-- Step 3: 任何人都可以读取
create policy "Public read"   on cards for select using (true);
-- 任何人都可以新增
create policy "Public insert" on cards for insert with check (true);
-- 任何人都可以删除（前端用管理员密码控制）
create policy "Public delete" on cards for delete using (true);

-- Step 4: 建立 Storage bucket（在 Supabase Dashboard > Storage 手动建立 "uploads" public bucket）
-- 或用以下 SQL：
insert into storage.buckets (id, name, public)
  values ('uploads', 'uploads', true)
  on conflict do nothing;

-- Storage 权限
create policy "Public upload" on storage.objects
  for insert with check (bucket_id = 'uploads');

create policy "Public read storage" on storage.objects
  for select using (bucket_id = 'uploads');

create policy "Public delete storage" on storage.objects
  for delete using (bucket_id = 'uploads');
