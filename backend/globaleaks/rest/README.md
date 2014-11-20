
## Messages

### Complex messages naming

The names of the messages used between globaleaks/handlers and
globaleaks/rest/responses.py and globaleaks/rest/requests.py follow certain rules
that, when learned, would easily make recognize the role of the messages.

**All the responses are composed by three section, every section has a keyword:**

**First**: destination domain 
  * public
  * admin
  * wb (whistleblower)
  * receiver
  * actors = wb + receiver (the users accessing a Tip)

**Second**: element described
  * Receiver
  * Context
  * Tip
  * Node
  * Profile
  * Comment

**Third**: data type 
  * Desc: a dictionary
  * List: the struct represented can be present 0 to N-th times
