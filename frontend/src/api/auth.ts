import api from './client'

export interface TokenResponse {
  access_token: string
  token_type: string
  username: string
}

export function register(username: string, password: string) {
  return api.post<TokenResponse>('/auth/register', { username, password })
}

export function login(username: string, password: string) {
  return api.post<TokenResponse>('/auth/login', { username, password })
}
