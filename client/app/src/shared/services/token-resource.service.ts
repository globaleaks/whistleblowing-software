import {Injectable} from "@angular/core";
import {HttpClient} from "@angular/common/http";
import {CryptoService} from "@app/shared/services/crypto.service";
import {Observable, from, switchMap} from "rxjs";

@Injectable({
  providedIn: "root"
})
export class TokenResource {

  private baseUrl = "api/token/:id";

  constructor(private cryptoService: CryptoService, private http: HttpClient) {
  }

  getToken(id: string) {
    this.http.post<any>(this.baseUrl.replace(":id", id), {}).subscribe();
  }

  getWithProofOfWork(): Observable<any> {
    return from(this.http.post("api/auth/token", {})).pipe(
      switchMap((response: any) => {
        const token = response;
        return this.cryptoService.proofOfWork(token.id).pipe(
          switchMap((answer: any) => {
            token.answer = answer;
            return new Observable<any>((observer) => {
              observer.next(token);
              observer.complete();
            });
          })
        );
      })
    );
  }
}