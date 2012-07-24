
The REST-spec.md specify a series of **DataTypes** that express 

  * File: file descriptor element, every file (uploaded or available in download) 
  * LocaLDict: the Local Dict is an object used to store localized texts
  * ReceiverDesc: Description of the received and the properties assigned
  * NodeProperties: series of tuple with boolean value, expressing the property
  * NodeStats: series of arrays containing the node statistics, the need to
  * FormFields: series of element describing an series of Field using keyword:
  * ModuleDataStruct: is an generic object used to describe flexible object in
  * GroupDescription: is an object used to describe a group of receivers, more than
  * TipStats: composite object containing the stats of  single Tip
  * TipIndex: this is the aggregation of the available Tip for a certain receiver.


# "class RestDataTypes", design and goals

Every elements exposed before would be represent by a python class who extend the class _RestDataTypes_, implemented in the file **RestJSONwrappers**, ad decorator function, able to guarntee debugging, security enforcing and detailed analysis of the data sent to the client.

Implementes as native methods:

  * security analysis and enforcing of the content sent to the client, this would be a point which apply santization, padding and other security measures.
  * utility for ORM interface, for the object who need them
  * incremental logging: permit to flush with the content of the object, with timestamp, when the object is complete or on demand.
  * logging utility for every RW access in the object, this would help during debug
  * diff: A decorator invoked a top of every set-get method, that check the previous value (if any), report the change.
  * extension: Check in the ymal schema. If the variable name is associated with a certain function, invoke that, those function can be implemented in an external module.
  * creation of generic JSON struct, useful from all the REST section that need to create a json obj.

Those utlities permit to develop checks (even extensions), tools and analysis from the point of view of the REST datatypes interaction.

Those methods permit, via configuration file, to enable a specific and detailed logging and tacking, extremely helpful in the development process.

## Required in every subclass

  * print JSON function, that extract the aquired data in the defined JSON format. Convert the collected data in JSON format, may trigger here exception for missing, invalid, malformed arguments.

## File

Take as costructor the filename (we would be sure that Storage Module would not change this logic, and shall relay only on framework that expose a VFS interface, [no URL, possibility to seek, read write stat])

'size' and 'data' parameters are missing, they are sets using stat().
All the other parameters (see REST-spec.md) are passed from the father codeflow.


## LocalDict

Take as constructor the key of the element (like: "message for the whistleblower #1" or "admin description of the modules #3", "error-code: 21"), open the dictionary and compile the dict based on the languages available.

## ReceiverDesc

  * Costructor take theID of the Receiver
  * "Configurable Boolean parameters" are managed in a signle call, _date values too
  * Other parameters are set-get in a dedicated call each.

## NodeProperties

  * Costructor that take all the boolean parameters.

## FormField

  * Name of the FORM take in the costructor
  * A call permit to add a sepecific field, never is delete a previous value, its just add.

## ModuleDataStruct

  * Costructor take the ID of the module
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.

# GroupDescription

  * Costructor take the ID of the group
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.

# TipStats

  * Costructor take the ID of the Tip enabling access
  * Others parameters are set-get in a dedicated call each.

# TipIndex

  * Costructor take the ID of the requested Tip
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.

# ContextDescription

  * Costructor take the ID of the context
  * _data values are managed in a signle call
  * Others parameters are set-get in a dedicated call each.
