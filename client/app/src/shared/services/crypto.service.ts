import {Injectable} from "@angular/core";
import {Observable, from} from "rxjs";
import {switchMap} from "rxjs/operators";
import sha256 from "fast-sha256";

@Injectable({
  providedIn: "root"
})
export class CryptoService {

  data: string;
  counter: number = 0;

  getWebCrypto(): SubtleCrypto | undefined {
    return typeof window !== "undefined" && window.isSecureContext
      ? window.crypto.subtle
      : undefined;
  }

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
    const webCrypto = this.getWebCrypto();

    if (webCrypto) {
      const toHash = this.str2Uint8Array(this.data + this.counter);
      const digestPremise = from(webCrypto.digest({name: "SHA-256"}, toHash));

      return digestPremise.pipe(
        switchMap((res) => this.calculateHash(res))
      );
    } else {
      return new Observable<number>((observer) => {
        const toHash = this.str2Uint8Array(this.data + this.counter);

        if (sha256(toHash)) {
          observer.next(0);
          observer.complete();
        } else {
          observer.error("error");
        }
      });
    }
  }

  proofOfWork(data: string): Observable<number> {
    this.data = data;
    this.counter = 0;
    return this.work();
  }
}
