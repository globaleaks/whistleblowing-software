=================
Integration guide
=================

This guide illustrates how GlobaLeaks can be integrated into an existing website.


Main components to integrate
----------------------------

There are two main components that need to be integrated into an initiative's website. They are:

- **Submission interface** (this lets a whistleblower make a new submission): /#/submission
- **Receipt interface** (this lets a whistleblower interact with an existing submission): /#/receipt

These are the main examples which are typically required. In general, though, every URL in GlobaLeaks can be embedded on the host's website. If the URL Parameter ?embedded=true is appended to a GlobaLeaks URL, the page's header and footer is removed and the page becomes embeddable within another page.

Integration modes
-----------------

Depending on the integration requirements, the following configurations are possible:


- Plugin based integration (suggested)

- iframe based integration


Plugin based integration
........................

GlobaLeaks provides a specific Javascript plugin to be used for integration. The platform makes it available at /js/plugin.js.
The plugin can be included on a website with a script tag like:

::

  <script type="text/javascript" src="https://PublicWebsite/globaleaks/js/plugin.js"></script>

The plugin safely loads the platform as a widget by calling the function StartGlobaLeaks().
This function can be used to embed specific platform resources. In the following example the submission interface is loaded when the link is clicked.

::

  <a href="javascript:startGlobaLeaks('https://PublicWebsite/globaleaks/#/submission')" style="text-decoration: none;">Blow the Whistle!</a>


Iframe based integration
........................

Using iframes to integrate GlobaLeaks into a website is not recommended because browsers are known to leak information about a whistleblowers browsing activity. However, *they have been used in the past in low-risk environments* and are worth mentioning. Including the two main components is similar to the plugin based solution discussed above.

**Submission interface**

::

  <iframe width="100%" height="100%" frameborder="0" src="https://PublicWebsite/#/submission?embedded=true"></iframe>


**Receipt Interface**

::

  <iframe width="100%" height="100%" frameborder="0" src="https://PublicWebsite/#/receipt?embedded=true"></iframe>


URL parameters
---------------------
There are several URL parameters that a web developer can use to change the GlobaLeaks platform's behaviour when integrating the platform into a website.


Language selection
..................

The lang URL parameter pre-selects the language used in the interface. The example below loads the submission interface in English.

::

  /#/submission?lang=en


Context selection
.................

The context URL parameter selects a specific submission context to load by passing a UUID. For example:

::

  /#/submission?context=06cb60d2-13a4-4aa3-926f-85b64f12239d


Note that a context's UUIDs can be found on the platform in the context configuration section of the administration interface.
