export interface FileResource {
  name: string;
  content?:string;
}

export interface FileResources {
  key: FileResource;
  cert: FileResource;
  chain: FileResource;
  csr: FileResource;
}