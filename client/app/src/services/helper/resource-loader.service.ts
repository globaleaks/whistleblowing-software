import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root',
})
export class ResourceLoaderService {

  // Function to dynamically load a stylesheet
  loadStyle(href: string): void {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = href;
    document.head.appendChild(link);
  }
}
