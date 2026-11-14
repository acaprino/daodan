export const fetchWithCsrf = async (url: string, options: RequestInit = {}) => {
    return fetch(url, options);
};
