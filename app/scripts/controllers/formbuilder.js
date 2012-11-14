function FormBuilderCtrl(){
    var scope = this;
    scope.newField = {};
    scope.fields = [{
        type: 'text',
        name: 'Name',
        placeholder: 'John Doe',
        order: 10
    }];
    scope.editing = false;
    scope.tokenize = function(slug1, slug2) {
        var result = slug1;
        result = result.replace(/[^-a-zA-Z0-9,&\s]+/ig, '');
        result = result.replace(/-/gi, "_");
        result = result.replace(/\s/gi, "-");
        if (slug2) {
            result += '-' + scope.token(slug2);
        }
        return result;
    };
    scope.saveField = function() {
        if (scope.newField.type == 'checkboxes') {
            scope.newField.value = {};
        }
        if (scope.editing !== false) {
            scope.fields[scope.editing] = scope.newField;
            scope.editing = false;
        } else {
            scope.fields.push(scope.newField);
        }
        scope.newField = { order: 0 };
    };
    scope.editField = function(field) {
        scope.editing = scope.fields.indexOf(field);
        scope.newField = field;
    };
    scope.splice = function(field, fields) {
        fields.splice(fields.indexOf(field), 1);
    };
    scope.addOption = function() {
        if (scope.newField.options === undefined) {
            scope.newField.options = [];
        }
        scope.newField.options.push({ order: 0 });
    };
    scope.typeSwitch = function(type) {
        if (angular.Array.indexOf(['checkboxes','select','radio'], type) === -1)
            return type;
        return 'multiple';
    }
}
