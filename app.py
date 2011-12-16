# GLBackend Dummy backend for testing GLClient
from flask import Flask, jsonify, request
from logging import FileHandler
dummy_tip_form = { 'type' : 2,
                  '0' : {'title': 'Help us fight Corruption!',
                         'fields': [{'name': 'tip', 
                                     'title': 'Your tip', 
                                     'description': 'Explain the issue in less than 3000 chars',
                                      'type': 'text',
                                      'size': '3000c',
                                      }],
                         'buttons': {'next': 'Add some files'}
                        },
                  '1' : {'title': 'Load Documents',
                         'fields': [{'name': 'files',
                                     'title': 'select files',
                                     'type': 'files'
                                     },
                                    {'name': 'documentDescription', 
                                     'title': 'Describe the documents', 
                                     'description': 'Explain the content of the uploaded material in less than 100 words',
                                      'type': 'text',
                                      'size': '100w',
                                      }
                                    ],
                         'buttons': {'next': 'Add more details', 
                                     'finish': 'Finalize the submission'}
                         },
                  '2' : {'title': '',
                         'fields': [
                                    {'name': 'someText1', 
                                     'title': 'Some Text', 
                                     'description': '',
                                      'type': 'text',
                                      'size': None,
                                      },
                                    {'name': 'someText2', 
                                     'title': 'Some Text', 
                                     'description': '',
                                      'type': 'string',
                                      'size': None
                                      },
                                    {'name': 'someText3', 
                                     'title': 'Some Text', 
                                     'description': '',
                                      'type': 'select',
                                      'options': [
                                                  ['Something', 'something'],
                                                  ['Something else', 'somethingelse']
                                                  ]
                                      },
                                    {'name': 'someText4', 
                                     'title': 'Some Text', 
                                     'description': '',
                                      'type': 'date',
                                      'size': None,
                                      },
                                    {'name': 'someText5', 
                                     'title': 'Some Text', 
                                     'description': '',
                                      'type': 'radio',
                                      'options': [
                                                  ['Option 1', 'opt1'],
                                                  ['Option 2', 'opt2'],
                                                  ['Option 3', 'opt3']
                                                  ],
                                      'size': None,
                                      }
                                    ]
                         }
                  }
                    
# This is a dummy tip that gives an idea of the structure of tips
dummy_tip = { 'receipt': "1234567890",
            'form': dummy_tip_form,
            'data': None
           }

class Tip(object):
    """dummy Tip model"""
    
    def __init__(self, tid = None):
        self.tid = tid

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 's3cr3tz!'

app.logger.addHandler(FileHandler("logfile.log"))

@app.route('/tip', methods=['POST'])
def create_tip():
    app.logger.debug("POST TIP")
    app.logger.debug("DATA: %s", jsonify(request.form))
    tip = dummy_tip
    return jsonify(tip)
    

@app.route('/tip/<tid>', methods=['GET'])
def read_tip(tid):
    app.logger.debug("GET TIP - TID: %s", tid)
    tip = dummy_tip
    return jsonify(tip)

@app.route('/tip/<tid>', methods=['PUT'])
def update_tip(tid):
    app.logger.debug("PUT TIP - TID: %s", tid)
    app.logger.debug("DATA: %s", jsonify(request.form))

@app.route('/tip/<tid>', methods=['DELETE'])
def delete_tip(tid):
    app.logger.debug("DELETE TIP - TID: %s", tid)

if __name__ == '__main__':
    app.run()

