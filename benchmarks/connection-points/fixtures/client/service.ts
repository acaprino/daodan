import { getApiPath } from './paths';
import { fetchWithCsrf } from './csrf';

const API_BASE = '/api';

export const listTasks = async (query: string) => {
    return fetch(getApiPath(`tasks${query}`), { credentials: 'include' });
};

export const deleteTask = async (uid: string) => {
    return fetch(getApiPath(`task/${encodeURIComponent(uid)}`), { method: 'DELETE' });
};

export const timeline = async (uid: string) => {
    return fetch(`${API_BASE}/task/${uid}/timeline`);
};

export const projects = async (state: string) => {
    let url = 'projects';
    if (state) url += `?state=${state}`;
    return fetch(getApiPath(url));
};

export const iterations = async (uid: string, from?: string) => {
    const url = from ? getApiPath(`task/${uid}/next?from=${from}`) : getApiPath(`task/${uid}/next`);
    return fetch(url);
};

const withQuery = (path: string, params: string) => (params ? `${path}?${params}` : path);

export const plan = async (date: string) => fetch(getApiPath(withQuery('daily-plan', date)));

async function send(path: string, method: string) {
    return fetch(getApiPath(path), { method, credentials: 'include' });
}

export const checkIn = (uid: string) => send(`habits/${uid}/check-in`, 'POST');

export const createUser = () => fetchWithCsrf(getApiPath('admin/users'), { method: 'POST' });

export const unknown = (fileUrl: string) => fetch(fileUrl);

export const avatar = (uid: string) => `<img src="${getApiPath(`users/${uid}/avatar`)}">`;
