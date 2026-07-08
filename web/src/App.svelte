<script lang="ts">
  import Router from './lib/router/Router.svelte';
  import { route, navigate } from './lib/router/router.svelte';
  import { auth, loadMe } from './lib/stores/auth.svelte';
  import Login from './routes/Login.svelte';

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
  <Router
    routes={{ '/login': login }}
    fallback={fallbackSnippet}
  />
{/if}

{#snippet login()}
  <Login />
{/snippet}

{#snippet fallbackSnippet()}
  {#if auth.status === 'authed'}
    <p class="p-6">Signed in as {auth.me?.username} — screens land in Tasks 4–7.</p>
  {:else}
    <Login />
  {/if}
{/snippet}
