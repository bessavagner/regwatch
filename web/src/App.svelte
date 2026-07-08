<script lang="ts">
  import Router from './lib/router/Router.svelte';
  import { route, navigate } from './lib/router/router.svelte';
  import { auth, loadMe } from './lib/stores/auth.svelte';
  import Login from './routes/Login.svelte';
  import Feed from './routes/Feed.svelte';
  import Watches from './routes/Watches.svelte';
  import Digests from './routes/Digests.svelte';

  const PUBLIC = new Set(['/login']);

  // Bootstrap: try to resume a session (also seeds csrf) on first load.
  $effect(() => {
    if (auth.status === 'idle') loadMe();
  });

  // Guard: unauthenticated access to a private route redirects to /login.
  $effect(() => {
    if (auth.status === 'anon' && !PUBLIC.has(route.path)) navigate('/login');
    if (auth.status === 'authed' && route.path === '/login') navigate('/feed');
  });
</script>

{#if auth.status === 'idle' || auth.status === 'loading'}
  <p class="p-6 text-muted">Loading…</p>
{:else}
  {#if auth.status === 'authed'}
    <nav class="flex items-center gap-1 border-b p-2 text-sm">
      <a href="/feed" class="rounded px-2 py-2.5 text-brand-600">Triage</a>
      <a href="/watches" class="rounded px-2 py-2.5 text-brand-600">Watches</a>
      <a href="/digests" class="rounded px-2 py-2.5 text-brand-600">Digests</a>
      <button class="ml-auto rounded px-2 py-2.5 text-muted" onclick={() => auth.logout().then(() => navigate('/login'))}>Log out</button>
    </nav>
  {/if}
  <Router
    routes={{ '/login': login, '/feed': feed, '/watches': watchesRoute, '/digests': digestsRoute }}
    fallback={fallbackSnippet}
    authed={auth.status === 'authed'}
    isPublic={(p) => PUBLIC.has(p)}
    login={login}
  />
{/if}

{#snippet login()}
  <Login />
{/snippet}

{#snippet feed()}
  <Feed />
{/snippet}

{#snippet watchesRoute()}
  <Watches />
{/snippet}

{#snippet digestsRoute()}
  <Digests />
{/snippet}

{#snippet fallbackSnippet()}
  {#if auth.status === 'authed'}
    <Feed />
  {:else}
    <Login />
  {/if}
{/snippet}
