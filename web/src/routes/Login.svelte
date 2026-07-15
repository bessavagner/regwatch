<script lang="ts">
  import Button from '../lib/ui/Button.svelte';
  import Input from '../lib/ui/Input.svelte';
  import Card from '../lib/ui/Card.svelte';
  import { auth } from '../lib/stores/auth.svelte';
  import { navigate } from '../lib/router/router.svelte';

  let username = $state('');
  let password = $state('');

  async function submit(e: SubmitEvent) {
    e.preventDefault();
    await auth.login(username, password);
    if (auth.status === 'authed') navigate('/feed');
  }
</script>

<main class="auth">
  <div class="auth__brand">
    <span class="wordmark">regwatch</span>
    <p class="eyebrow mt-4 text-xs opacity-60">00 · access</p>
    <h1 class="hero__title mt-2">sign in to start <em>watching</em>.</h1>
    <p class="hero__lede mt-3">
      regwatch checks every new Diário Oficial da União publication against your
      watches — the moment it's published.
    </p>
  </div>

  <div class="auth__form">
    <Card>
      <p class="eyebrow mb-4 text-xs opacity-60">01 · sign in</p>
      <form onsubmit={submit} class="space-y-3">
        <div>
          <label for="username" class="mb-1 block text-sm text-ink-2">Username</label>
          <Input id="username" bind:value={username} />
        </div>
        <div>
          <label for="password" class="mb-1 block text-sm text-ink-2">Password</label>
          <Input id="password" type="password" bind:value={password} />
        </div>
        {#if auth.error}
          <p role="alert" class="text-sm text-danger">{auth.error}</p>
        {/if}
        <Button type="submit">Sign in</Button>
      </form>
    </Card>
  </div>
</main>
