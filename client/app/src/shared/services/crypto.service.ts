import {Injectable} from "@angular/core";
import {Observable, from} from "rxjs";
import {switchMap} from "rxjs/operators";
import * as sodium from 'libsodium-wrappers-sumo';
@Injectable({
  providedIn: "root"
})
export class CryptoService {
  data: string;
  counter: number = 0;

  calculateHash(hash: any): Observable<number> {
    hash = new Uint8Array(hash);
    if (hash[31] === 0) {
      return new Observable<number>((observer) => {
        observer.next(this.counter);
        observer.complete();
      });
    } else {
      this.counter += 1;
      return this.work();
    }
  }

  str2Uint8Array(str: string): Uint8Array {
    const result = new Uint8Array(str.length);
    for (let i = 0; i < str.length; i++) {
      result[i] = str.charCodeAt(i);
    }
    return result;
  }

  work(): Observable<number> {
    const webCrypto = window.crypto.subtle;

    const toHash = this.str2Uint8Array(this.data + this.counter);
    const digestPremise = from(webCrypto.digest({name: "SHA-256"}, toHash));

    return digestPremise.pipe(
      switchMap((res) => this.calculateHash(res))
    );
  }

  proofOfWork(data: string): Observable<number> {
    this.data = data;
    this.counter = 0;
    return this.work();
  }
  
  async generateSalt(username: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(username);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = new Uint8Array(hashBuffer);
    const saltArray = hashArray.slice(0, 16);
    const saltBase64 = btoa(String.fromCharCode(...saltArray));

    return saltBase64;
  }
  
  async hashArgon2(password: string, usename: string, usersalt?:string): Promise<string> {
    const passwordBytes = sodium.from_string(password);
    const salt = usersalt ? usersalt : await this.generateSalt(usename);
    const binaryString = atob(salt);
    const saltBytes = Uint8Array.from(binaryString, char => char.charCodeAt(0));
    const truncatedSalt = saltBytes.slice(0, 16);

    const hash = sodium.crypto_pwhash(
      32,
      passwordBytes,
      truncatedSalt,
      16,
      1 << 27,
      sodium.crypto_pwhash_ALG_ARGON2ID13
    );

    return sodium.to_base64(hash, sodium.base64_variants.ORIGINAL);
  }
}
