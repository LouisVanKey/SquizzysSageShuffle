# Getting the Hero Picker online, step by step (free, no programming)

You need three free accounts: GitHub (hosts the page), Supabase (stores the hero locks) and Discord (login).
Plan about 30 minutes. Button names on these sites change now and then; if one is slightly different, look for the closest match.

Keep a notepad open. You will collect five values along the way:

- A. your site address
- B. Supabase Project URL
- C. Supabase anon (publishable) key
- D. Discord Client ID
- E. Discord Client Secret (keep this one private)

## Part 1: Put the site on GitHub (10 min)

1. Unzip `squizzys-sage-shuffle.zip` on your computer.
2. Go to https://github.com and create an account (or log in).
3. Top right: **+** > **New repository**. Name it `squizzys-sage-shuffle`, choose **Public**, click **Create repository**.
4. On the new page click the link **uploading an existing file**.
5. Open the unzipped folder, select everything *inside* it (`index.html`, `css`, `js`, `assets`, `supabase`, ...) and drag it
   onto the GitHub page. Wait for the upload, then click **Commit changes**.
6. In the repository go to **Settings** > **Pages**. Under "Branch" choose **main** and **/ (root)**, click **Save**.
7. After a minute or two the same page shows your address: `https://YOUR-NAME.github.io/squizzys-sage-shuffle/`.
   Write it down as **A**. Open it: the site works, with a "Demo mode" label (picks are not shared yet).

## Part 2: Create the database on Supabase (10 min)

1. Go to https://supabase.com, click **Start your project** and sign up (signing in with GitHub is easiest).
2. **New project**: any name, let it generate a database password (save it somewhere), region **Europe**, plan **Free**.
   Wait until the project is ready.
3. In the left menu open **SQL Editor**.
4. On your computer open `supabase/schema.sql` with Notepad / TextEdit, copy everything, paste it in the SQL Editor
   and click **Run**. It should say "Success".
5. Clear the editor, do the same with `supabase/seed_heroes.sql`, click **Run**.
6. Open **Project Settings** (gear icon) > **API** (or the **Connect** button at the top). Write down:
   - **B**: the Project URL, like `https://abcdefgh.supabase.co`
   - **C**: the key called **anon** / **publishable**. Not the `service_role` / secret key.

## Part 3: Set up Discord login (10 min)

1. In Supabase open **Authentication** > **Sign In / Providers** > **Discord**. Leave this tab open.
   It shows a **Callback URL**, like `https://abcdefgh.supabase.co/auth/v1/callback`. Copy it.
2. In a new tab go to https://discord.com/developers/applications and log in. Click **New Application**,
   name it `Squizzy's Sage Shuffle`, create it.
3. In the left menu open **OAuth2**.
   - Copy the **Client ID** (**D**).
   - Click **Reset Secret**, copy the secret (**E**).
   - Under **Redirects** click **Add Redirect**, paste the Callback URL from step 1, click **Save Changes**.
4. Back in the Supabase tab: switch Discord to **enabled**, paste **D** and **E**, click **Save**.
5. Still in Supabase: **Authentication** > **URL Configuration**.
   - **Site URL**: paste **A**.
   - **Redirect URLs**: click **Add URL**, paste **A** again. Save.

## Part 4: Connect the site to the database (3 min)

1. On GitHub open your repository, click the folder `js`, then the file `config.js`.
2. Click the pencil icon (**Edit this file**).
3. Put **B** and **C** between the empty quotes, so it looks like:

   ```js
   supabaseUrl: "https://abcdefgh.supabase.co",
   supabaseAnonKey: "eyJhbGciOi...long text...",
   ```

   You can also change the event date and venue here.
4. Click **Commit changes**. Wait two minutes, then reload your site (**A**). "Demo mode" should be gone.

## Part 5: Make yourself organiser (3 min)

1. In the Discord app: **User Settings** > **Advanced** > turn on **Developer Mode**.
2. Right-click your own name anywhere in Discord > **Copy User ID** (a long number). Do the same for Brecht.
3. In Supabase > **SQL Editor**, run this with your numbers:

   ```sql
   insert into public.admins (discord_id, note) values ('111111111111111111', 'Louis'), ('222222222222222222', 'Brecht');
   ```

## Part 6: Test it

1. Open your site and click **Log in with Discord**. Approve. You should see "Welcome, <your name>".
2. Lock a hero and enjoy the animation.
3. Open the site in a private/incognito window: your hero is under "Locked in" with your name and Discord tag.
4. As organiser you see a **Remove** button under each locked hero. Use it to remove your test pick.
5. Share the link (**A**) in your Discord.

## If something goes wrong

- **Still says Demo mode**: `config.js` was not saved correctly (check the quotes and commas), or wait a few more minutes and hard-reload.
- **Discord shows "Invalid OAuth2 redirect_uri"**: the redirect in the Discord application is not exactly the Supabase Callback URL.
- **After approving you return to the site but are not logged in**: address **A** is missing in Supabase > Authentication > URL Configuration.
- **"Could not lock hero"**: `schema.sql` or `seed_heroes.sql` was not run, or ran with an error. Run them again; it is safe.
- **No Remove button**: your Discord User ID is not in the `admins` table, or you need to log out and in again.

Managing, changing and deleting picks during the event is explained in `README.md` under "Managing the locks".
