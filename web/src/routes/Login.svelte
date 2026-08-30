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
    <p class="eyebrow mt-4 text-xs opacity-60">00 · acesso</p>
    <h1 class="hero__title mt-2">entre para começar a <em>monitorar</em>.</h1>
    <p class="hero__lede mt-3">
      o regwatch confere cada nova publicação do Diário Oficial da União com as
      suas buscas — assim que ela sai.
    </p>
  </div>

  <div class="auth__form">
    <Card>
      <p class="eyebrow mb-4 text-xs opacity-60">01 · entrar</p>
      <form onsubmit={submit} class="space-y-3">
        <div>
          <label for="username" class="mb-1 block text-sm text-ink-2">usuário</label>
          <Input id="username" bind:value={username} />
        </div>
        <div>
          <label for="password" class="mb-1 block text-sm text-ink-2">senha</label>
          <Input id="password" type="password" bind:value={password} />
        </div>
        {#if auth.error}
          <p role="alert" class="text-sm text-danger">{auth.error}</p>
        {/if}
        <Button type="submit">entrar</Button>
      </form>
    </Card>
  </div>
</main>
