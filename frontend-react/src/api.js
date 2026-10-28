
let session = { accessToken: "", user: null };

export const getSession = () => session;

export function clearSession() {
  session = { accessToken: "", user: null };
}

function authorizationHeaders() {
  return session.accessToken
    ? { Authorization: `Bearer ${session.accessToken}` }
    : {};
}

export async function request(path, options = {}) {
  const isPublic =
    (path === "/posts" || /^\/posts\/[^/]+$/.test(path)) &&
    (!options.method || options.method === "GET");

  const isLogin = path === "/auth/login";

  const response = await fetch(`/api${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(!isPublic && !isLogin ? authorizationHeaders() : {}),
      ...options.headers,
    },
  });

  const data = response.status === 204
    ? null
    : await response.json();

  if (!response.ok) {
    if (response.status === 401 && !isLogin) {
      clearSession();
    }

    const error = new Error(
      data?.message || data?.code || `HTTP ${response.status}`
    );

    error.status = response.status;
    error.code = data?.code;
    throw error;
  }

  return data;
}

export async function login(email, password) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  session = {
    accessToken: data.accessToken,
    user: data.user,
  };

  return data.user;
}

export function canEdit(post) {
  return Boolean(
    post &&
    session.user &&
    Number(post.authorId) === Number(session.user.id)
  );
}

export const api = {
  list: () => request("/posts"),
  detail: (id) => request(`/posts/${id}`),

  create: (input) =>
    request("/posts", {
      method: "POST",
      body: JSON.stringify(input),
    }),

  update: (id, input) =>
    request(`/posts/${id}`, {
      method: "PUT",
      body: JSON.stringify(input),
    }),

  remove: (id) =>
    request(`/posts/${id}`, {
      method: "DELETE",
    }),

  me: () => request("/me"),
};
