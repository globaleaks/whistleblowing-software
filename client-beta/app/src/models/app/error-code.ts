export class ErrorCodes {
  message: string = "";
  arguments = [];
  code: number = -1;

  constructor(protected messageParam?: any,protected codeParam?: any,protected  argumentParam?: any) {
    this.message = messageParam;
    this.arguments = argumentParam;
    if (codeParam) {
      this.code = codeParam;
    }
  }
}