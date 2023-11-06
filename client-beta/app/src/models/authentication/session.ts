export interface Session {
  id: string;
  role: string;
  encryption: boolean;
  user_id: string;
  session_expiration: number;
  properties: Properties;
  homepage: string;
  preferencespage: string;
}

export interface Properties {
}