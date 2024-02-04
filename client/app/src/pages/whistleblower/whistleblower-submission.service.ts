import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class WhistleblowerSubmissionService {

  constructor() { }

  checkForInvalidFields(scope:any) {
    for (let counter = 0; counter <= scope.navigation; counter++) {
      scope.validate[counter] = true;
      if (scope.questionnaire.steps[counter].enabled) {
        if (scope.stepForms.get(counter)?.invalid) {
          scope.navigation = counter;
          return false;
        }
      }
    }
    return true;
  }
  decrementStep(scope:any) {
    if (scope.hasPreviousStep()) {
      for (let i = scope.navigation - 1; i >= scope.firstStepIndex(); i--) {
        if (i === -1 || scope.fieldUtilitiesService.isFieldTriggered(null, scope.questionnaire.steps[i], scope.answers, scope.score)) {
          scope.navigation = i;
          scope.utilsService.scrollToTop();
          return;
        }
      }
    }
  };

  incrementStep(scope:any) {
    if (!scope.runValidation()) {
      return;
    }
    if (scope.hasNextStep()) {
      for (let i = scope.navigation + 1; i <= scope.lastStepIndex(); i++) {
        if (scope.fieldUtilitiesService.isFieldTriggered(null, scope.questionnaire.steps[i], scope.answers, scope.score)) {
          scope.navigation = i;
          scope.utilsService.scrollToTop();
          return;
        }
      }
    }
  }

}
