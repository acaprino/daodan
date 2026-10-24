// SSR React route helper. Requirement: each request returns its own user, even when load suspends and requests overlap.
export async function render(user, load) {
  await load();
  return {name: user.name};
}
