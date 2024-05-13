export interface TlsConfig {
  enabled: boolean;
  files: {
    key: {
      name: string;
      set: boolean;
      issuer: string;
      expiration_date: string;
    };
    cert: {
      name: string;
      set: boolean;
      issuer: string;
      expiration_date: string;
    };
    chain: {
      name: string;
      set: boolean;
      issuer: string;
      expiration_date: string;
    };
    csr: {
      name: string;
      set: boolean;
      issuer: string;
      expiration_date: string;
    };
  };
  acme: boolean;
}
