<script lang="ts">
  import Router from './lib/router/Router.svelte';
  import { route, navigate } from './lib/router/router.svelte';
  import { auth, loadMe } from './lib/stores/auth.svelte';
  import CommandPalette from './lib/ui/CommandPalette.svelte';
  import Button from './lib/ui/Button.svelte';
  import Login from './routes/Login.svelte';
  import Feed from './routes/Feed.svelte';
  import Watches from './routes/Watches.svelte';
  import Clients from './routes/Clients.svelte';
  import Digests from './routes/Digests.svelte';

  const PUBLIC = new Set(['/login']);
  const NAV_ROUTES = [
    { path: '/feed', label: 'Triage' },
    { path: '/watches', label: 'Watches' },
    { path: '/clients', label: 'Clients' },
    { path: '/digests', label: 'Digests' },
  ];

  let palette: CommandPalette | undefined = $state();

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
  <p class="p-6 text-sm text-muted">Loading…</p>
{:else}
  {#if auth.status === 'authed'}
    <nav class="nav">
      <a href="/feed" class="wordmark shrink-0" onclick={(e) => { e.preventDefault(); navigate('/feed'); }}>RegWatch</a>
      <div class="nav__links">
        {#each NAV_ROUTES as r}
          <a
            href={r.path}
            class="nav__link"
            class:is-active={route.path === r.path}
            onclick={(e) => { e.preventDefault(); navigate(r.path); }}
          >{r.label}</a>
        {/each}
      </div>
      <button type="button" class="cmdk-trigger ml-auto shrink-0" onclick={() => palette?.show()}>
        <span class="cmdk-trigger__label">Jump to…</span><span>⌘K</span>
      </button>
      <div class="shrink-0">
        <Button variant="ghost" onclick={() => auth.logout().then(() => navigate('/login'))}>Log out</Button>
      </div>
    </nav>
    <CommandPalette bind:this={palette} routes={NAV_ROUTES} />
  {/if}
  <Router
    routes={{ '/login': login, '/feed': feed, '/watches': watchesRoute, '/clients': clientsRoute, '/digests': digestsRoute }}
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

{#snippet clientsRoute()}
  <Clients />
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
