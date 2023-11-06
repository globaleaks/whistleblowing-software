import {ComponentFactoryResolver, Directive, Input, ViewContainerRef} from "@angular/core";
import {ImageUploadComponent} from "@app/shared/partials/image-upload/image-upload.component";

@Directive({
  selector: "[appImageUpload]",
})
export class ImageUploadDirective {
  @Input() imageUploadModel: any;
  @Input() imageUploadModelAttr: string;
  @Input() imageUploadId: string;
  @Input() imageSrcUrl: string;

  constructor(private viewContainerRef: ViewContainerRef, private componentFactoryResolver: ComponentFactoryResolver) {
  }

  ngOnInit() {
    const componentFactory = this.componentFactoryResolver.resolveComponentFactory(ImageUploadComponent);
    const componentRef = this.viewContainerRef.createComponent(componentFactory);
    const dynamicComponentInstance = componentRef.instance;

    dynamicComponentInstance.imageUploadModel = this.imageUploadModel;
    dynamicComponentInstance.imageUploadModelAttr = this.imageUploadModelAttr;
    dynamicComponentInstance.imageUploadId = this.imageUploadId;

  }
}
