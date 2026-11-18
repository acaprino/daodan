const API_SERVER_URL = import.meta.env.PUBLIC_API_SERVER_URL;
const PAGE_SIZE = 12;

export async function fetchDogs(currentPage: number) {
  const response = await fetch(`${API_SERVER_URL}/api/dogs?page=${currentPage}&per_page=${PAGE_SIZE}`);
  return response.json();
}

export async function fetchDog(dogId: number) {
  const response = await fetch(`${API_SERVER_URL}/api/dogs/${dogId}`);
  return response.json();
}

export async function fetchBreed(breed: string) {
  const response = await fetch(`${API_SERVER_URL}/api/breeds/${breed}`);
  return response.json();
}

export async function fetchAny(path: string) {
  const response = await fetch(`${API_SERVER_URL}${path}`);
  return response.json();
}
