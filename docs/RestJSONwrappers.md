
The REST-spec.md specify a series of **DataTypes** that express 

  * fileDict: file descriptor element, every file (uploaded or available in download) 
  * localizationDict: the Local Dict is an object used to store localized texts
  * receiverDescriptionDict: Description of the received and the properties assigned
  * nodePropertiesDict: series of tuple with boolean value, expressing the property of the Node
  * nodeStatisticsDict: series of arrays containing the node statistics, **need to be defined**.
  * formFieldsDict: definition of the input field for a certain input kind, from the submission to the module confuguration.
  * moduleDataDict: is an generic object used to describe the object implemented in the modules
  * groupDescriptionDict:  is an object used to describe a group of receivers, and the module configured to manage them. More than one group is possibile in a single context. more than one receiver is possible in a context. a receiver has only one group.
  * contextDescriptionDict: is an object used to describe a context.
  * tipIndexDict: this is the aggregation of the available Tip for a certain receiver.
  * tipStatistics: composite object containing the stats of single Tip, and all the reference for data


# "class RestJSONwrapper", design and goals

Every elements exposed before would be represent by a python class who extend the class _RestDataTypes_, implemented in the file **RestJSONwrappers**, ad decorator function, able to guarntee debugging, security enforcing and detailed analysis of the data sent to the client.

Implementes as native methods:

  * security analysis and enforcing of the content sent to the client, this would be a point which apply santization, padding and other security measures.
  * incremental logging: permit to flush with the content of the object, with timestamp, when the object is complete or on demand.
  * logging utility for every RW access in the object, this would help during debug
  * diff: A decorator invoked a top of every set-get method, that check the previous value (if any), report the change.
  * extension: Check in the ymal schema. If the variable name is associated with a certain function, invoke that, those function can be implemented in an external module.
  * creation of generic JSON struct, useful from all the REST section that need to create a json obj.
  * verify that all the expected field are present (no typing enforcement at the moment)

Those utlities permit to develop checks (even extensions), tools and analysis from the point of view of the REST datatypes interaction.

Those methods permit, via configuration file, to enable a specific and detailed logging and tacking, extremely helpful in the development process.

## Testing ad usage

TODO: actually a working prototype and test case of fileDict, localizationDict, receiverDescriptionDict, genericDict is implemented in globaleaks/utils/JSONhelper.py

## Required in every subclass

  * print JSON function, that extract the aquired data in the defined JSON format. Convert the collected data in JSON format, may trigger here exception for missing, invalid, malformed arguments.

## fileDict

Take as costructor the filename (we would be sure that Storage Module would not change this logic, and shall relay only on framework that expose a VFS interface, [no URL, possibility to seek, read write stat])

'size' and 'data' parameters are missing, they are sets using stat().
All the other parameters (see REST-spec.md) are passed from the father codeflow.

Implement the methods:

  * content_type
  * comment
  * metadata

## localizationDict

Take as constructor the key of the element (like: "message for the whistleblower #1" or "admin description of the modules #3", "error-code: 21"), open the dictionary and compile the dict based on the languages available.

How localized dict are handled:

    { 'TheTitleOFThePage': 
        { 'IT' : 'Benvenuti',
          'EN' : 'Welcome" }
    }

    The key is "TheTitleOFThePage", is a keyword used to address at all the translation available for a certain segment.

Implement two method for adding a localization in a JSON obj:

  * add_translation: await for a new keyword and the appropriate dict of translation
  * add_language: require an existing keyword ("TheTitleOFThePage"), and add a new { 'LG' : 'TranslationForLGlanguage' }

## receiverDescriptionDict

  * Costructor take theID of the Receiver
  * "Configurable Boolean parameters" are managed in a signle call, _date values too
  * Other parameters are set-get in a dedicated call each.

Implemented except the CBP, to be done.

## genericDict

An object able to handle generic key/value 
   * Constructor take an identificative name of the object, useful when triggered the debug
   * mothods are: add_integer, add_string, add_dict

## nodePropertiesDict

  * Costructor that take all the boolean parameters.
  * Others parameters are set-get in a dedicated call each.

## formFieldsDict

  * Name of the FORM take in the costructor
  * A call permit to add a sepecific field, never is delete a previous value, its just add.

## moduleDataDict

  * Costructor take the ID of the module
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.

## groupDescriptionDict

  * Costructor take the ID of the group
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.

## contextDescriptionDict

  * Costructor take the ID of the context
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.
  * if CBP would be apply to a single context, they need to be moved here instead of in nodePropertiesDict

## tipStatistics

  * Costructor take the ID of the Tip enabling access
  * Others parameters are set-get in a dedicated call each.

## tipInexDict

  * Costructor take the ID of the requested Tip
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.
