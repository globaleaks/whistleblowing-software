'use strict';

var forEach = angular.forEach;

describe('GLClient', function() {

  var deleteReceivers = function() {

    browser().navigateTo('#/admin/receivers');

    element('div[ng-controller="AdminReceiversCtrl"]').query(function(receivers, done){

      var children = receivers.find('.receiverList');
      
      if ( children.length > 0 ) {
        element('.receiverList .deleteReceiver').click();
      }
      
      if ( children.length > 1 ) {
        deleteReceivers();
      }
      
      done();
    });
  };

  var addRandomReceiver = function() {
    browser().navigateTo('#/admin/receivers');

    var receiver_count = repeater('.receiverConfig').count(),
      rand_num = Math.round(Math.random()*1000),
      receiver_email = "foo"+rand_num+"@bar.com",
      receiver_added = false;

    input('new_receiver.name').enter("Test Receiver " + rand_num);
    input('new_receiver.email').enter(receiver_email);
    input('new_receiver.password').enter("Antani1234");

    element('.addReceiver button').click();

    element('.receiverList').query(function(tbody, done){
      forEach(tbody.find('input[name="email"]'), function(email){
        if ( email.value == receiver_email ) {
          receiver_added = true;
        }
      });
      
      expect({value: receiver_added}).toBe(true);
      
      done(); 
    });
  };

  beforeEach(function() {
      browser().navigateTo('/index.html');
  });

  describe('Admin interface', function() {

    beforeEach(function() {

      browser().navigateTo('#/login');
      input('loginUsername').enter('admin');
      input('loginPassword').enter('globaleaks');
      element('button.btn').click();

      browser().reload();

      browser().navigateTo('#/admin/content');
      
    });

    describe('Admin Receivers', function() {

      it('Should allow to add a receiver', function(){
        //deleteReceivers();

        addRandomReceiver();
        addRandomReceiver();
        addRandomReceiver();
        addRandomReceiver();
      });

    // it('Should allow to configure a receiver', function(){
    //   var receiver_count = repeater('.receiverConfig').count(),
    //     receiver = repeater('.receiverConfig').row(0);
    //   window.antani = receiver;
    //   receiver.input('receiver.notification_fields.mail_address').enter('testing@foo.com');
    //   receiver.element('.btn').click();

    //   browser().navigateTo('#/admin/basic');
    //   receiver = repeater('.receiverConfig').row(0);

    //   expect(receiver.input('receiver.notification_fields.mail_address').val()).toBe('testing@foo.com');
    // });

    });

    describe('Admin Contexts', function() {

      it('Should allow to add a context', function(){

        browser().navigateTo('#/admin/contexts');

        var receiver_count = repeater('.receiverConfig').count();

        input('new_context_name').enter("Test Context");
        element('.addContext button').click();


        using('form[name=contextForm]').input('context.name').enter("Some name");
        using('form[name=contextForm]').input('context.description').enter("Some description");

        //using('form[name=contextForm]').select('context.name').value("Something");
        var receiver_id = using('form[name=contextForm]').element('option').val();
        using('form[name=contextForm]').input('context.name').enter("Something");
        
        element('.selectionDetails').click();
        element('.editButtons .btn-success').click();

      });

    });

  });


  // describe('Submission interface', function() {

  //   it('Should allow to select a context', function() {
  //     browser().navigateTo('#/submission');

  //     expect(repeater('.contexts option').count()).toBe(2);
  //     select('submission.current_context').option('0');

  //     expect(repeater('.receiverCard').count()).toBe(2);

  //   });

  //   it('Should allow to select receivers', function() {

  //   });

  // });

});
