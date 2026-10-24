// SSR React route helper. Requirement: each request returns its own user, even when load suspends and requests overlap.
let currentUser;
export async function render(user, load) {
  currentUser = user;
  await load();
  return {name: currentUser.name};
}
